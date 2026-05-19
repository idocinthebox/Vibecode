# Packet 6/7 Code Review — Findings

Date: 2026-05-18
Commit: 8909851 (`main`)
Reviewer: GitHub Copilot (agent)
Methodology: Graphify-first (used `graphify-out/graph.json` for module/complexity inventory) + Vibecoder `/memory/inject` to seed prior failure patterns + targeted spot-reads only on highest-risk surfaces. Token spend minimised by avoiding full-tree reads. Local Vibecode service reachable (HTTP 200 on `/health`).

## Scope reviewed

Backend:
- [vibecode/api/middleware.py](vibecode/api/middleware.py), [vibecode/api/app.py](vibecode/api/app.py), [vibecode/api/routes_pro.py](vibecode/api/routes_pro.py), [vibecode/api/routes_memory.py](vibecode/api/routes_memory.py)
- [vibecode/services/injection_service.py](vibecode/services/injection_service.py)
- [vibecode/integrations/pro_sync.py](vibecode/integrations/pro_sync.py)
- [vibecode/jobs/confidence_decay.py](vibecode/jobs/confidence_decay.py)
- [vibecode/core/memory_service.py](vibecode/core/memory_service.py) (Phase 4/8 sections)
- [vibecode/config/settings.py](vibecode/config/settings.py)

Pro server:
- [server/pro/main.py](server/pro/main.py), [server/pro/db/schema.py](server/pro/db/schema.py), [server/pro/routes/contributions.py](server/pro/routes/contributions.py), [server/pro/routes/search.py](server/pro/routes/search.py), [server/pro/routes/moderation.py](server/pro/routes/moderation.py)

Extension:
- [vibe-code-extension/src/services/terminalRecallService.ts](vibe-code-extension/src/services/terminalRecallService.ts), [vibe-code-extension/src/commands/shareToDatabankCommand.ts](vibe-code-extension/src/commands/shareToDatabankCommand.ts)

---

## Severity-ranked findings

### 🚨 CRITICAL

1. **Confidence decay scheduler is never started.**
   `start_decay_scheduler()` in [vibecode/jobs/confidence_decay.py](vibecode/jobs/confidence_decay.py#L59) has zero call sites in production code (only the function's own docstring references it). `confidence_decay_interval_hours` in [vibecode/config/settings.py](vibecode/config/settings.py#L39) is also unused. Net effect: the Packet 6 "background decay" feature is dead code in shipped builds.
   - Fix: call `start_decay_scheduler(get_data_dir(), interval_hours=settings.confidence_decay_interval_hours)` from `create_app()` (or a `@app.on_event("startup")` hook) in [vibecode/api/app.py](vibecode/api/app.py).
   - Also: `_decay_loop` sleeps **before** the first call ([vibecode/jobs/confidence_decay.py#L51](vibecode/jobs/confidence_decay.py#L51)); even when wired up there will be no decay for the first interval. Run once eagerly, then enter the loop.

2. **Pro server accepts arbitrary, unauthenticated, unredacted submissions.**
   `POST /databank/contributions` ([server/pro/routes/contributions.py](server/pro/routes/contributions.py)) has no auth, no rate limit, and stores the caller's `data` dict verbatim as `body_json` with no secret redaction. Combined with `submitted_by: str = "anonymous"`, anyone with network access can flood the databank or submit secrets-bearing payloads.
   - Fix: require Bearer-token auth (mirror `ProSyncAdapter` headers); call `redact_secrets()` server-side on every text field; cap `body_json` size; rate-limit per IP/token.

### ⚠️ HIGH

3. **`pro_share` does not redact secrets before sending to the Pro databank.**
   [vibecode/core/memory_service.py#L939](vibecode/core/memory_service.py#L939) copies the full DB row into `data` and forwards it through `ProSyncAdapter.submit`. Patterns may contain raw error output / paths / tokens. The docstring of `ProSyncAdapter.submit` even warns "caller must redact first" — but the caller does not.
   - Fix: run `redact_secrets()` over all string fields (especially `failure_reason`, `bad_suggestion`, `corrected_approach`, `reasoning_summary`) before submitting.

4. **`ProShareRequest.project_path` is accepted but ignored — no allowlist check on share.**
   [vibecode/api/routes_pro.py#L37](vibecode/api/routes_pro.py#L37). Sharing a memory bypasses the per-project allowlist that the rest of the surface enforces. A misconfigured agent on a disallowed project can still publish patterns from that project.
   - Fix: pass `project_path` into `service.pro_share(...)` and reject with `PROJECT_NOT_ALLOWED` when not on the allowlist.

5. **`terminalRecallService` sends a synthetic error string, not the real terminal output.**
   [vibe-code-extension/src/services/terminalRecallService.ts#L65](vibe-code-extension/src/services/terminalRecallService.ts#L65) posts `error_output: \`Command failed: ${command}\`` because `onDidEndTerminalShellExecution` does not expose stdout/stderr text. As a result `recall_on_error` only ever searches against the command line itself, defeating the "match the error" intent — recall will be very noisy or empty.
   - Fix: either use Shell Integration `execution.read()` (async iterable of bytes, available on recent VS Code) to capture the last N lines, or document the limitation and rename the field to `command_text`.

6. **Pro `_moderate("escalate")` sets state back to `pending`.**
   [server/pro/routes/moderation.py#L70](server/pro/routes/moderation.py#L70). Escalation should be a distinct state (e.g. `escalated`) so reviewers can filter it; otherwise escalated items get re-served by `moderation_queue` and may bounce back and forth indistinguishably from new submissions. The schema CHECK constraint also forbids any value other than `pending|approved|rejected`, so even if you tried to set `escalated` today it would raise.
   - Fix: extend `review_state` CHECK to include `escalated`, and use it.

7. **Running service is stale relative to disk.**
   `GET /openapi.json` on the running 0.3.0 service lists no `/pro/*`, no `/memory/check-command`, no `/memory/recall-on-error`, and no `/reports/tokens/buckets`, although all four are defined on disk. The Phase 6/7 surface will not be reachable until `vibecode service restart` is run after install. There is no version sanity-check that warns when a stale service is bound to port 8765.
   - Fix: bump `FastAPI(version=…)` per packet and have `vibecode doctor` warn when the service-reported version is older than the installed package version.

### ⚙️ MEDIUM

8. **`RateLimitMiddleware` leaks memory and lacks `Retry-After`.**
   [vibecode/api/middleware.py#L30](vibecode/api/middleware.py#L30) keeps a `deque` per `(client_ip, path)` tuple forever. Even on localhost this grows unbounded across distinct query strings… actually `scope["path"]` excludes query string, so growth is bounded by route count × client IPs (small). Still: there is no eviction of empty deques and no `Retry-After` header in 429 responses, which is mandatory per RFC 6585 and helps clients self-throttle.
   - Fix: drop empty deques when the window empties; emit `Retry-After: 60`.

9. **`_get_client_ip` honours `X-Forwarded-For` unconditionally.**
   [vibecode/api/middleware.py#L40](vibecode/api/middleware.py#L40). Comment says "informational" because the service is localhost-only, but the value is still returned as the bucket key, letting a single malicious local process bypass the limit by rotating that header. Either ignore the header for rate limiting, or only honour it when the connection comes from a trusted proxy.

10. **`pro_share` strips fields by hard-coded blacklist.**
    [vibecode/core/memory_service.py#L946-L956](vibecode/core/memory_service.py#L946). Using a deny-list (`is_active`, `content_hash`, `agent_source`, `source_ref`) means any new sensitive column added to the schema later is implicitly published. Prefer an explicit allow-list of shareable fields, or a `to_dict_public()` method on the model.

11. **`InjectionService._merge_and_rerank` dedupes on title only.**
    [vibecode/services/injection_service.py#L210](vibecode/services/injection_service.py#L210). Titles collide easily across teams ("Use Depends() in FastAPI"). Two semantically different patterns can be merged. Use `(memory_type, title.lower(), language)` as the dedup key, or a content hash.

12. **`pro_search` / `pro_status` leak raw exception messages.**
    `ProSyncAdapter` returns `{"error": str(exc)}` which `VibeCodeService.pro_*` and the route handlers pass straight through to the client. Network errors include host info / paths. Normalise to a stable code + generic message; log details server-side.

13. **`_search_remote` silently swallows Pro errors.**
    [vibecode/services/injection_service.py#L107](vibecode/services/injection_service.py#L107) returns `[]` on `"error" in payload`. The agent never learns the Pro databank is down. Surface a soft warning section in the injected markdown (e.g. `## Pro Databank Unavailable`) instead of pretending it returned nothing.

14. **httpx calls are synchronous inside the (sync) Pro adapter and called from sync FastAPI handlers.**
    Fine today because FastAPI offloads sync defs to a threadpool, but each Pro call blocks one worker thread for up to 10s. Under load this halves your effective concurrency. Either switch to `httpx.AsyncClient` and `async def` handlers, or document a connection-pool limit.

15. **`shareToDatabankCommand` exposes a free-form `memoryId` input.**
    [vibe-code-extension/src/commands/shareToDatabankCommand.ts#L23](vibe-code-extension/src/commands/shareToDatabankCommand.ts#L23). Users must paste a UUID, which is hostile UX *and* means there is no client-side check that the ID belongs to the current project. Replace with a `QuickPick` populated from the pattern browser / review queue.

16. **Pro server search ranking is naive substring + tiny usefulness term.**
    [server/pro/routes/search.py#L48](server/pro/routes/search.py#L48). Loads every approved pattern into memory each request, scores by `sum(t in text)`. Will not scale beyond a few thousand approved patterns. Add a FTS5 virtual table (already trivial with SQLite) and `LIMIT` the candidate set.

### ℹ️ LOW / NIT

17. `routes_pro.pro_share` declares `request: ProShareRequest` but never reads it (apart from satisfying schema). Either remove the body or use `request.project_path`.
18. `vibecode/api/middleware.py` lacks `Retry-After` and the limit value isn't surfaced in headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`).
19. `confidence_decay.run_once` opens its own connection — good — but doesn't `WAL` checkpoint after large updates; harmless but worth noting.
20. Pro `databank_status` exposes the pending count to anyone — fine if auth is added (finding #2), otherwise it's information disclosure.
21. The shipped graph (`graphify-out/graph.json`) is stale — it has 0 nodes for `pro_sync`, `middleware`, `confidence_decay`, `routes_pro`, `server/pro/**`, `terminalRecallService`, `shareToDatabankCommand`. Rebuild as part of the release process so token-saving agents (this review!) can rely on it.
22. There are two on-disk copies of `vibe-code-extension/` (one under `d:\Vibecode\`, the canonical git-tracked one under `d:\Vibecoder\`). Confirmed via injected Vibecoder memory. Reviewed only the git-tracked copy; consider deleting or symlinking the duplicate.

---

## Test coverage assessment

Targeted slice passed earlier (35 tests). What's missing:

- No test exercises the **decay scheduler actually starting** when the app boots (would catch finding #1).
- No test asserts that `pro_share` redacts secrets (finding #3) or enforces allowlist (finding #4).
- No test for `terminalRecallService` (the field semantics in #5 would have surfaced).
- No Pro-server auth test (because there is no auth — finding #2).

## Recommended follow-ups (in order)

1. Wire the decay scheduler into `create_app()` and add an integration test (`tests/test_decay_scheduler_startup.py`) that boots the app, monkeypatches `time.sleep`, and asserts `run_once` was called.
2. Add `redact_secrets()` on the `pro_share` path; assert in a test.
3. Add Bearer-token auth + per-token rate limit to `server/pro/*`; ship a `PRO_API_TOKEN` env var.
4. Pass and enforce `project_path` in `pro_share`.
5. Add `escalated` to the Pro schema CHECK and to the moderation queue filter.
6. Bump `FastAPI(version=…)` to `0.4.0` (or the next packet number) and add a doctor warning when the running service is older than installed package.
7. Replace `terminalRecallService` synthetic error string with Shell Integration `execution.read()`; or rename API field.
8. Rebuild `graphify-out/` as part of release.

---

## Methodology note (token savings)

- Used **Vibecoder `/memory/inject`** once (≈1.5k tokens) instead of re-reading prior session notes.
- Used **graphify** (`vc_funcs=827, vc_classes=125`) to identify top-15 complexity hotspots and confirm Phase 6/7 file presence; flagged 0-node entries as either stale graph or missing files, then verified on disk with one `Get-ChildItem`.
- Read 12 source files (most ≤ 200 lines) targeted by graph + memory hints — no blanket directory sweeps.
- No edits to production code in this pass; review only.
