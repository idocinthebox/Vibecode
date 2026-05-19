# Codex Build Brief — Unified Packet 6 + 7

This is a one-page kickoff brief for handing the Unified Packet 6+7 build to
**OpenAI Codex** (or any non-Copilot coding agent). Paste the **System
Prompt** below into Codex's instructions, then point it at the **Task List**.

Full spec lives in [Build_Packet_6_7_Unified.md](Build_Packet_6_7_Unified.md).
Known gotchas live in [Known_Issues.md](Known_Issues.md).

---

## System Prompt (paste into Codex)

```text
You are building features for the VibeCode local AI coding memory service.

WORKSPACE
- Repo root: d:\Vibecoder  (NOTE THE 'r' — d:\Vibecode without the 'r' is a
  scratch sibling and has no venv, no git, no editable install. ALL commands
  must run from d:\Vibecoder.)
- Activate venv before any python/pytest/vibecode commands:
    cd d:\Vibecoder
    .\.venv\Scripts\Activate.ps1
- Tests: pytest tests/ -q
- Lint: ruff check vibecode/ tests/
- Type-check: mypy vibecode/

LIVE MEMORY SERVICE
A FastAPI service runs on http://127.0.0.1:8765 (localhost-only, no auth).
Before non-trivial edits, query it:
  POST /memory/search        body: {"project_path":"d:\\Vibecoder","query":"<task>","limit":5}
  POST /memory/inject        body: {"project_path":"d:\\Vibecoder","query":"<task>"}
On test/build failure:
  POST /memory/capture-failure  body: see vibecode/api/schemas.py CaptureFailureRequest
On test/build success after a fix:
  POST /memory/capture-success  body: see CaptureSuccessRequest in same file
Keep request bodies SHORT and avoid backticks / unusual punctuation in long
fields — the FastAPI body parser has been observed to reject large bodies
with `"There was an error parsing the body"` (see Docs/Known_Issues.md item
about capture-failure parse errors). Prefer plain ASCII prose.

PROCESS RULES
1. Before editing files under vibecode/cli/service.py, vibecode/api/, or
   anything touching the service lifecycle, READ Docs/Known_Issues.md first.
2. Never run `vibecode service stop` and assume it worked. It is best-effort
   and does NOT kill the daemon. Verify with:
     Get-NetTCPConnection -LocalPort 8765 -State Listen | Select OwningProcess
   If a stale PID exists, restart cleanly: Stop-Process -Id <pid> -Force then
   `vibecode service start` from d:\Vibecoder.
3. Do NOT touch Pro Databank / shared-publish code paths in a way that
   auto-publishes anything. Local-first; sharing requires explicit human opt-in.
4. After each phase, write a short report to Docs/reports/ with: commits,
   tests, follow-ups. Do not skip this step.
5. PowerShell quoting: do not embed `"` inside single-quoted strings passed
   to native exes — write a `.tmp_<name>.ps1` script for any multi-statement
   or multi-quoted invocation, then delete it after.

WHAT TO BUILD
Follow the phased plan in Docs/Build_Packet_6_7_Unified.md §9. Do NOT start
Phase N+1 until Phase N's exit criteria pass. Detailed per-phase prompts are
already drafted in §13 of that same doc — use them verbatim where they exist.
```

---

## API Quick Reference

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness + storage check |
| POST | `/memory/search` | Find existing patterns/rules |
| POST | `/memory/inject` | Build a context block for an upcoming task |
| POST | `/memory/capture-failure` | Record a failed approach + prevention rule |
| POST | `/memory/capture-success` | Record a working approach (correlate with prior failure via `task_intent`) |
| POST | `/memory/pre-edit-check` | Pre-edit policy check |
| POST | `/rules/add` | Add a project rule |
| POST | `/reports/tokens` | Token-savings report |
| POST | `/observe/edit\|diagnostic\|test\|revert\|terminal` | Telemetry events |

Schemas: [vibecode/api/schemas.py](../vibecode/api/schemas.py).
Routes: [vibecode/api/routes_memory.py](../vibecode/api/routes_memory.py),
[vibecode/api/routes_observe.py](../vibecode/api/routes_observe.py),
[vibecode/api/routes_health.py](../vibecode/api/routes_health.py).

---

## Phase-Ordered Task List

Each phase ships independently. Block on its exit criteria before starting the next.

### Phase 0 — Shared Foundations  *(prereq for everything)*

- Schema migrations (Build_Packet_6_7_Unified.md §6).
- Extend `vibecode/core/security.py` redaction (Mongo URIs, `xoxb-`, JWT, AWS session tokens).
- New `AuditLogRepository` writing to `audit_log`.
- Pydantic length limits (`code_*` ≤ 10000, `task_intent` ≤ 500, `tags` ≤ 50).
- Path-traversal validators on `project_path` / `file_path`.
- **Exit:** migrations applied, redaction unit tests pass, every capture/search/inject path emits one audit row.

### Phase 1 — Harvester MVP

- `KnowledgeHarvester` service + walkers: `DocSourceWalker`, `ClaudeMdExtractor`, `MarkdownRuleExtractor`.
- Normalizer, dedupe, review-queue writer, JSON report → `.vibecode/harvest_report.json`.
- Routes: `POST /harvest/scan`, `POST /harvest/preview`, `GET /harvest/report`.
- CLI: `vibecode harvest scan|preview|report|sources`.
- **Exit:** scanning the VibeCode repo itself yields ≥ 20 candidates; no dupes on re-run; all writes audited.

### Phase 2 — Harvester Full Source Coverage

- Add `ADRExtractor`, `ChangelogFixExtractor`, `LinterConfigExtractor`, `InlineCommentExtractor`.
- Embedding-based near-dupe detection (no-op if embeddings unavailable).
- Extension UX: command, first-run prompt, sidebar review group, post-scan webview.
- **Exit:** scanning a repo with CHANGELOG + ADRs produces correctly typed failure patterns and architecture rules; manual UX check on the Vibecoder workspace.

### Phase 3 — Pro Databank Server

- Pro API per [Build_Packet_6_Pro_Shared_Databank.md](Build_Packet_6_Pro_Shared_Databank.md) §5–6.
- Moderation queue worker with SLA timers.
- Postgres + pgvector schema, embedding ingestion job.
- Server-side tests with fake Pro token.
- **Exit:** contribute → moderate (approve) → search → retract round-trip works end-to-end against local Docker Postgres.

### Phase 4 — Pro Sync Adapter (client)

- `vibecode/integrations/pro_sync.py`: submit / search / feedback / retract.
- Per-item "Share to databank" opt-in in CLI + extension (NEVER auto-publish).
- Merge order in `InjectionService`: local → team → global, with `local_first_boost`.
- Settings: `vibeCode.pro.enabled`, `vibeCode.pro.scopes`, `vibeCode.pro.endpoint`, `vibeCode.pro.token` (VS Code secret storage).
- **Exit:** confirmed harvested rule can be shared with one click, appears in `POST /databank/search`, merged behind local results in `inject_context`.

### Phase 5 — Telemetry, Hardening, Final Report

- Token-savings report split into `local`, `harvested`, `shared_team`, `shared_global` buckets via audit log.
- Per-endpoint rate limiting on capture / inject / search / observe / harvest.
- Confidence-decay background job (every 6h).
- `vibecode doctor` extended with harvester + Pro health rows.
- Final report per §12, committed under `Docs/reports/`.
- **Exit:** §11 acceptance criteria all pass.

---

## Pre-Flight Checklist (do once before unleashing Codex)

1. **Service running detached** — closing the build terminal must not kill it:

   ```powershell
   Start-Process -FilePath ".\.venv\Scripts\python.exe" `
     -ArgumentList "-m","vibecode","service","start" `
     -WorkingDirectory "d:\Vibecoder" -WindowStyle Hidden
   Start-Sleep 2
   Invoke-WebRequest http://127.0.0.1:8765/health -UseBasicParsing | Select StatusCode
   ```

   Expect `200`.
2. **Branch off main:** `git checkout -b feature/packet-6-7-phase-0`.
3. **Baseline tests green:** `pytest tests/ -q`.
4. **Allowlist confirmed:** `vibecode service status` shows `allowed_projects_count >= 1` and the repo is in it.
5. Codex has been given (a) the system prompt above, (b) read access to `Docs/`, `vibecode/`, `tests/`, (c) shell access from `d:\Vibecoder`.

When Phase 0 ships green, repeat from step 2 for Phase 1, etc.
