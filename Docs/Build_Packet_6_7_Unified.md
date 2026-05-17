# Build Packet 6 + 7 (Unified): Pro Shared Databank & Project Knowledge Harvester

## Senior Build Packet

Project: VibeCode - Token-Efficient AI Coding Memory Layer
Phases: 6 (Pro Shared Databank) and 7 (Project Knowledge Harvester), delivered together as one program.
Purpose: Make VibeCode able to (a) ingest knowledge that already exists in a project's documents, memory files, and rule files, and (b) optionally share that knowledge through a moderated, privacy-safe Pro databank for community + team retrieval.
Target Builder: Codex (primary) / GPT-5.5 / Claude Opus / Cursor Agent
Difficulty: Advanced
Estimated Build Time: 40-60 hours total, phased
Prerequisites: Packets 1, 1B, 2, 3A, 4A, 4B, 4C, 5 complete and green.

---

## 1. Why Combine Packet 6 and Packet 7

The two features share the same core data path: produce high-quality typed memory items, run them through redaction, dedupe, confidence scoring, and a review queue, and then expose them through retrieval. Packet 7 is the strongest possible feeder for Packet 6:

1. Harvester (P7) extracts rules / failure+fix pairs / facts from local project documents into typed VibeCode memory.
2. Pro Databank (P6) optionally publishes opted-in items, runs moderation, and serves merged retrieval back into agents.

Building them in one program lets the shared `harvest_meta`, `source_ref`, `review_state`, redaction pipeline, and audit log be designed once instead of twice.

---

## 2. Executive Summary

### Packet 7 - Project Knowledge Harvester (local)

Scans known knowledge surfaces in a workspace (CLAUDE.md, AGENTS.md, .github/copilot-instructions.md, .cursor/rules/**, README, ADRs, CHANGELOG, docs/**, linter configs, marked inline comments), classifies each finding as a `project_rule`, `success_pattern`, or `failure_pattern`, redacts secrets, dedupes, confidence-scores, and writes results into the existing review queue with full `source_ref` provenance.

### Packet 6 - Pro Shared Databank (optional, Pro-only)

Adds an opt-in pipeline so Pro users can contribute selected local items (manual or harvested) to a moderated global or team databank, and so retrieval can merge local + team + global with local-first ranking.

### Joint design constraints

1. Local memory remains primary. Nothing in Packet 6 or 7 may degrade local retrieval latency or correctness.
2. Both pipelines write to the **same review queue and use the same redaction + dedupe services**.
3. Everything harvested or shared carries `source_type` and `source_ref` so origin is auditable.
4. Sharing is **always explicit, per-item, opt-in**. Harvest alone never publishes.

---

## 3. Unified Design Principles

1. Local-first retrieval never regresses.
2. Explicit opt-in for every upload (Packet 6).
3. Provenance on every item (`source_type`, `source_ref`).
4. Redact, hash, minimize before any network call.
5. Deterministic extractors over LLM-generated rules.
6. Confidence-gated promotion: auto-confirm only above threshold.
7. Reversible: every harvested or published item can be retracted.
8. One review queue, one audit log, one redaction pipeline.

---

## 4. Unified Scope

### In Scope

- Harvester source walker, extractor registry, normalizer, dedupe, review-queue writer, reporter.
- Pro auth + entitlement checks, contribution pipeline, shared retrieval, moderation queue.
- Shared schema additions used by both features (`source_type`, `source_ref`, `harvest_meta`, `review_state`, `shared_publication`).
- CLI commands: `vibecode harvest ...`, `vibecode pro ...`.
- VS Code commands and webviews for both surfaces.
- Telemetry: token savings attributable to harvested vs shared items.

### Out of Scope (this program)

- Billing implementation details (assume Pro entitlement is already verifiable).
- LLM-driven rule synthesis (Phase 6 stretch only, behind a flag).
- Real-time collaboration / social features (comments, follows).
- Automatic code application from shared results.
- Cross-org private federation.

---

## 5. High-Level Architecture

~~~text
Workspace docs ──► KnowledgeHarvester (P7)
                     │
                     ▼
              Normalizer + Redactor + Dedupe (shared)
                     │
                     ▼
              Review Queue (existing) ──► Local Memory Stores
                                              │
                                              │ user opts an item in
                                              ▼
                                       Pro Sync Adapter (P6)
                                              │
                                              ▼
                                 Shared Databank API (P6)
                                  ├── Moderation Pipeline
                                  └── Postgres + pgvector store

Agent prompt build ──► InjectionService
                          ├── Local retrieval (always)
                          ├── Team retrieval   (if Pro + opted in)
                          └── Global retrieval (if Pro + opted in)
                          → merge + rerank (local-first) → top K
~~~

---

## 6. Shared Schema Additions (Phase 0)

Applies to both `success_patterns`, `failure_patterns`, `project_rules` tables.

| Column | Type | Notes |
|---|---|---|
| `source_type` | text | e.g. `manual`, `auto_capture`, `harvest:claude_md`, `harvest:adr`, `harvest:changelog`, `harvest:linter`, `harvest:inline_comment`, `shared:global`, `shared:team` |
| `source_ref` | text | `relative/path.md#L42-L57` for harvested; `submission_id` for shared |
| `harvest_meta` | json | `{ "extractor": "...", "rule_class": "...", "raw_confidence": 0.62 }` |
| `review_state` | text | `pending` \| `confirmed` \| `discarded` (already present for some tables; backfill where missing) |
| `shared_publication_id` | text nullable | links to `shared_publications` row if published |

New table `shared_publications`:

| Column | Type |
|---|---|
| `id` | text PK (`pub_01J...`) |
| `local_pattern_id` | text |
| `memory_type` | text |
| `scope` | text (`global` / `team:<id>`) |
| `submission_id` | text |
| `moderation_state` | text |
| `published_at` | timestamptz nullable |
| `retracted_at` | timestamptz nullable |

New table `audit_log` (used by both features):

| Column | Type |
|---|---|
| `id` | uuid PK |
| `ts` | timestamptz |
| `actor` | text (`cli`, `extension`, `mcp`, `harvester`, `pro_sync`) |
| `action` | text (`capture`, `harvest_write`, `publish`, `retract`, `moderate`, `search`, `inject`) |
| `target_type` | text |
| `target_id` | text |
| `project_path` | text |
| `meta` | json |

---

## 7. Packet 7 - Knowledge Harvester Spec

### 7.1 Source discovery

Default include list:

~~~text
CLAUDE.md, AGENTS.md, README.md, CONTRIBUTING.md,
.github/copilot-instructions.md,
.cursor/rules/**, .windsurfrules, .aider.conf.yml,
docs/**, Docs/**, ARCHITECTURE.md, STYLEGUIDE.md,
docs/adr/**, *.adr.md,
CHANGELOG.md,
pyproject.toml, .eslintrc*, .editorconfig, mypy.ini, ruff.toml
~~~

Walker rules:

1. Honor `.gitignore` and a new `.vibecodeignore`.
2. Skip files > 1 MB or detected binary.
3. Cap total files per scan at `harvest.max_files` (default 500).
4. Project path must pass the existing project allowlist.

### 7.2 Extractor registry

| Extractor | Targets | Produces |
|---|---|---|
| `ClaudeMdExtractor` | CLAUDE.md, AGENTS.md, copilot-instructions.md, cursor rules | `project_rule` |
| `MarkdownRuleExtractor` | Generic *.md inside docs/** + README | `project_rule`, `failure_pattern` |
| `ADRExtractor` | docs/adr/**, *.adr.md | `project_rule` (Accepted only) |
| `ChangelogFixExtractor` | CHANGELOG.md | `failure_pattern` |
| `LinterConfigExtractor` | pyproject.toml, .eslintrc*, etc. | low-severity `project_rule` |
| `InlineCommentExtractor` | source files with `VC-RULE:` / `# NOTE rule:` markers | `project_rule` |

### 7.3 Heuristics (deterministic, no LLM required)

1. Lines starting with `Always`, `Never`, `Do not`, `Don't`, `Prefer`, `Use ... instead of`, `Required:`, `Must` → `project_rule`. Severity: `must`/`never` → high, `prefer` → medium, `consider`/`may` → low.
2. Markdown headings containing `bug`, `pitfall`, `gotcha`, `anti-pattern`, `common mistake` → `failure_pattern`. The block body is `failure_reason`. The first fenced code block beneath is `bad_suggestion`. If a sibling block has `Fix:` / `Solution:` it becomes `prevention_rule` / `corrected_approach`.
3. CHANGELOG sections under `### Fixed`, `### Security`, `### Breaking` → `failure_pattern` with the fix line as `prevention_rule`.
4. ADRs: parse `Status:`, `Context`, `Decision`, `Consequences`. Status=`Accepted` → `project_rule(rule_type=architecture)`. Status=`Superseded`/`Rejected` → discard.
5. Linter configs: each explicitly enabled rule becomes a low-severity `project_rule(rule_type=style)`.
6. Inline comments matching `(VC-RULE|# NOTE rule|// NOTE rule):\s*(.+)` → `project_rule` at configured severity.
7. Code fences adjacent to a rule are attached as `code_after` (success) or `bad_suggestion` (failure).

### 7.4 Confidence formula

~~~text
confidence = 0.4 * source_weight
           + 0.3 * signal_strength
           + 0.2 * recency
           + 0.1 * specificity
~~~

| Term | Definition |
|---|---|
| `source_weight` | CLAUDE.md / AGENTS.md = 0.9, ADR(Accepted) = 0.85, changelog-fix = 0.7, README = 0.6, linter = 0.55, inline-comment = 0.5 |
| `signal_strength` | imperative verb + code example + rationale → 1.0; bullet only → 0.5 |
| `recency` | `exp(-age_days / 180)` based on file mtime or commit date |
| `specificity` | +boost if language/framework/identifier detected |

Default `harvest.auto_confirm_threshold = 0.8`. Items above → `confirmed`. Items below → `pending` in the review queue.

### 7.5 Dedupe

1. Compute `content_hash = sha256(normalize(text))` where `normalize` lowercases, strips whitespace, removes punctuation runs.
2. If exact hash matches an existing item, increment `occurrence_count` and skip create.
3. If `EmbeddingService` is available, compute cosine similarity vs items with the same `memory_type` + `language`. Threshold 0.92 → treat as duplicate.
4. Otherwise create new item with `review_state` decided by confidence threshold.

### 7.6 API

`POST /harvest/scan`

~~~json
{
  "project_path": "D:/Vibecoder",
  "include": ["**/*.md", "CLAUDE.md", "AGENTS.md", ".cursor/rules/**"],
  "exclude": ["node_modules/**", ".venv/**", "out/**"],
  "max_files": 500,
  "auto_confirm_threshold": 0.8,
  "dry_run": false
}
~~~

Response:

~~~json
{
  "scanned_files": 87,
  "candidates": 132,
  "auto_confirmed": 41,
  "queued_for_review": 91,
  "duplicates_skipped": 17,
  "report_id": "harv_01J...",
  "report_path": ".vibecode/harvest_report.json"
}
~~~

`POST /harvest/preview` - same body with `dry_run:true`, returns the candidate list without writing.

`GET /harvest/report?id=...` - returns the stored report.

### 7.7 CLI

1. `vibecode harvest scan --project . [--dry-run] [--auto-confirm 0.8]`
2. `vibecode harvest preview --project .`
3. `vibecode harvest report [--id harv_...]`
4. `vibecode harvest sources --list`

### 7.8 Extension UX

1. Command `VibeCode: Harvest Project Knowledge`.
2. First-run prompt on workspace open if `harvest.runOnInit` and CLAUDE.md / AGENTS.md / ADRs detected.
3. Sidebar group `Harvested (Pending)` inside the review queue with bulk-confirm by category.
4. Webview summary after each scan: counts by extractor, top 10 highest-confidence items, link to full report.

### 7.9 Settings

~~~json
"vibeCode.harvest.enabled": true,
"vibeCode.harvest.runOnInit": true,
"vibeCode.harvest.autoConfirmThreshold": 0.8,
"vibeCode.harvest.maxFiles": 500,
"vibeCode.harvest.sources": [
  "CLAUDE.md","AGENTS.md","README.md","CONTRIBUTING.md",
  ".github/copilot-instructions.md",".cursor/rules/**",".windsurfrules",
  "docs/**","Docs/**","CHANGELOG.md","ARCHITECTURE.md","docs/adr/**"
]
~~~

---

## 8. Packet 6 - Pro Shared Databank Spec

Use the existing Packet 6 spec (`Docs/Build_Packet_6_Pro_Shared_Databank.md`) as the authoritative reference for:

1. Auth and headers.
2. Endpoints: `POST /databank/contributions`, `POST /databank/search`, `POST /databank/feedback`, `GET /databank/contributions/{id}`, `POST /databank/retract`, moderation endpoints.
3. Postgres + pgvector schema.
4. Ranking formula and default weights.
5. Moderation workflow, SLAs, and audit fields.
6. Rollout plan.

This unified packet adds the following deltas:

1. Contribution submission must populate `local_pattern_id`, `source_type`, `source_ref` from the originating local item.
2. Items whose `source_type` starts with `harvest:` may be contributed only after the user has explicitly confirmed them in the review queue.
3. `shared_publications` table (Section 6) replaces the ad-hoc "publication tracking" mentioned in Packet 6.
4. All publish / retract / moderate actions write to the shared `audit_log` (Section 6).
5. Retrieval merge order: local → team → global, with `local_first_boost = +0.25` added to local scores during rerank.

---

## 9. Phased Delivery Plan

Each phase is independently shippable. Do not start phase N+1 until phase N's exit criteria are met.

### Phase 0 - Shared Foundations

1. Schema migrations for new columns and tables (Section 6).
2. Extend `vibecode/core/security.py` redaction patterns (Mongo URIs, Slack `xoxb-`, JWT, AWS session tokens).
3. New `AuditLogRepository` writing to `audit_log`.
4. Length limits on Pydantic schemas (`code_*` ≤ 10000, `task_intent` ≤ 500, `tags` ≤ 50).
5. Path-traversal validators on `project_path` / `file_path`.

Exit criteria: migrations applied, redaction unit tests pass for new patterns, every existing capture/search/inject path writes one audit row.

### Phase 1 - Harvester MVP

1. `KnowledgeHarvester` service with `DocSourceWalker`, `ClaudeMdExtractor`, `MarkdownRuleExtractor`, normalizer, dedupe, review-queue writer, JSON report writer to `.vibecode/harvest_report.json`.
2. `POST /harvest/scan` + `POST /harvest/preview` + `GET /harvest/report`.
3. CLI: `vibecode harvest scan|preview|report|sources`.

Exit criteria: scanning the VibeCode repo itself produces ≥ 20 candidates, no duplicates created on re-run, all writes audited.

### Phase 2 - Harvester Full Source Coverage

1. Add `ADRExtractor`, `ChangelogFixExtractor`, `LinterConfigExtractor`, `InlineCommentExtractor`.
2. Embedding-based near-duplicate detection (if embeddings available; otherwise no-op).
3. Extension command + first-run prompt + sidebar review group + post-scan webview.

Exit criteria: scanning a repo with CHANGELOG and ADRs produces correctly typed failure patterns and architecture rules; extension UX verified manually on Vibecoder workspace.

### Phase 3 - Pro Databank Server

1. Pro API service implementing all endpoints in `Build_Packet_6_Pro_Shared_Databank.md` Sections 5 and 6.
2. Moderation queue worker with SLA timers.
3. Postgres + pgvector schema, embedding ingestion job.
4. Server-side tests with a fake Pro token.

Exit criteria: contribute → moderate (approve) → search → retract round-trip works end-to-end against a local Docker Postgres.

### Phase 4 - Pro Sync Adapter (client)

1. `vibecode/integrations/pro_sync.py` with submit, search, feedback, retract.
2. Local opt-in workflow: per-item "Share to databank" action in CLI + extension; never auto-publish.
3. Retrieval merge in `InjectionService`: local → team → global with `local_first_boost`.
4. Settings: `vibeCode.pro.enabled`, `vibeCode.pro.scopes`, `vibeCode.pro.endpoint`, `vibeCode.pro.token` (secret storage).

Exit criteria: a confirmed harvested rule can be shared with one click, appears in `POST /databank/search`, and is merged behind local results during `inject_context`.

### Phase 5 - Telemetry, Hardening, Final Report

1. Token-savings report split into `local`, `harvested`, `shared_team`, `shared_global` buckets via the audit log.
2. Per-endpoint rate limiting middleware applied to capture/inject/search/observe/harvest.
3. Confidence-decay background job (every 6h).
4. `vibecode doctor` extended with harvester + Pro health rows.
5. Final report (Section 12) generated and attached to the release.

Exit criteria: all acceptance criteria in Section 11 pass; final report committed under `Docs/reports/`.

---

## 10. Testing Requirements

Tests are mandatory exit criteria for every phase. Use the existing pytest + mocha layout.

### 10.1 Phase 0

1. `tests/test_audit_log_repository.py` - insert + query by actor/action/target.
2. `tests/test_secret_redaction.py` - add cases: MongoDB SRV, Slack bot tokens, JWT, AWS session token.
3. `tests/test_schema_limits.py` - oversize fields rejected with 422.
4. `tests/test_path_traversal.py` - `..` and non-absolute paths rejected.
5. Alembic migration test: upgrade head + downgrade one step.

### 10.2 Phase 1

1. `tests/harvest/test_walker.py` - .gitignore + .vibecodeignore + size cap + max_files.
2. `tests/harvest/test_claude_md_extractor.py` - golden fixture in `tests/fixtures/harvest/CLAUDE.md` produces expected rule list.
3. `tests/harvest/test_markdown_rule_extractor.py` - imperative verbs, pitfall blocks with Fix sibling.
4. `tests/harvest/test_dedupe.py` - same content twice → one row + incremented occurrence_count.
5. `tests/harvest/test_confidence.py` - formula values match a hand-computed fixture.
6. `tests/test_http_harvest_routes.py` - `/harvest/scan`, `/harvest/preview`, `/harvest/report` happy path + auth + project allowlist.
7. `tests/cli/test_harvest_cli.py` - `vibecode harvest scan --dry-run` prints expected summary.

### 10.3 Phase 2

1. Extractor unit tests for ADR, Changelog, Linter, InlineComment (one fixture each).
2. `tests/harvest/test_near_dup.py` - cosine ≥ 0.92 deduped; below threshold kept.
3. Extension mocha tests:
   - `test/suite/harvestCommand.test.ts` - command runs, webview opens, sidebar group populated.
   - `test/suite/harvestSidebar.test.ts` - bulk-confirm flips review_state.

### 10.4 Phase 3

1. `tests/databank/test_contributions.py` - submit → dedupe_status, validation rules (pii_risk_score, title/summary lengths).
2. `tests/databank/test_moderation.py` - approve / reject / escalate transitions; SLA timer queued.
3. `tests/databank/test_search.py` - ranking honors local-first boost when client sends mixed scopes.
4. `tests/databank/test_retract.py` - retract removes from search index.
5. `tests/databank/test_pgvector.py` - embedding insert + nearest-neighbor query against Docker Postgres.

### 10.5 Phase 4

1. `tests/test_pro_sync_adapter.py` - submit/search/feedback/retract mocked at httpx layer.
2. `tests/test_injection_merge.py` - given mocked local + team + global results, the merge produces local-first order with the documented boost.
3. Extension mocha: `proShareCommand.test.ts` - "Share to databank" gated by opt-in; never fires on unconfirmed items.

### 10.6 Phase 5

1. `tests/test_token_report_buckets.py` - buckets sum to the audit log and never double-count prevention hits.
2. `tests/test_rate_limit_middleware.py` - per-route limits enforced; 429 returned with `retry_after_sec`.
3. `tests/test_confidence_decay_job.py` - patterns aged > 30d see confidence drop per formula; job idempotent.
4. `tests/test_doctor_extended.py` - new rows appear and surface failures correctly.

### 10.7 Cross-cutting requirements

1. All new tests must run under the existing `pytest` and `npm test` invocations with no extra flags.
2. No test may require network access except those marked `@pytest.mark.pro_server` which run against the Docker Postgres + the local Pro server fixture.
3. Coverage gate: each new module ≥ 85% line coverage.
4. All new endpoints must have a contract test that validates the response envelope from Packet 6 Section 5.

---

## 11. Acceptance Criteria (program-level)

1. Local retrieval p95 latency does not regress more than 10% vs the Packet 5 baseline.
2. No item is ever published without an explicit user action.
3. Every harvested or shared item has a resolvable `source_ref`.
4. `vibecode doctor` reports OK on a clean install with harvester enabled and Pro disabled.
5. `vibecode doctor` reports OK on a Pro-enabled install pointed at the Docker Pro server fixture.
6. All Phase 1-5 tests green on Windows and Linux runners.
7. The shared `audit_log` records every capture, harvest write, publish, retract, moderate, search, and inject.
8. Token-savings report attributes savings to the correct bucket (local / harvested / shared_team / shared_global) for a scripted end-to-end scenario.

---

## 12. Final Report (required deliverable at end of Phase 5)

Write `Docs/reports/Packet_6_7_Final_Report.md` containing:

1. **Summary** - what shipped, version numbers, commit hashes per phase.
2. **Architecture diagram** - rendered or ASCII, matching Section 5.
3. **Acceptance matrix** - each criterion in Section 11 marked Pass/Fail with evidence link (test name, log path, or screenshot).
4. **Test results** - pytest and mocha summary counts per phase; coverage report.
5. **Performance numbers** - p50/p95 for `inject_context`, `search`, `pre_edit_check`, `harvest/scan` (1k-file repo), `databank/search` (10k-item store).
6. **Security review** - redaction patterns added, audit log sample, path-traversal tests, rate-limit verification.
7. **Token-savings measurement** - scripted scenario showing tokens saved attributed by bucket.
8. **Known limitations** - explicit list.
9. **Migration / rollback notes** - alembic head + how to downgrade.
10. **Next steps** - candidate items for Packet 8.

---

## 13. Codex Build Prompts

Because the program spans 40+ hours of work and touches schema, server, client, and extension, **a single monolithic prompt is not recommended**. Use one prompt per phase, in order. Each prompt is self-contained and assumes the previous phase is merged.

### 13.0 Phase 0 Prompt - Shared Foundations

~~~text
You are extending the VibeCode repository (Python FastAPI + SQLite/Postgres backend, TypeScript VS Code extension). Implement Phase 0 of `Docs/Build_Packet_6_7_Unified.md`.

Scope:
1. Add Alembic migrations creating `audit_log` and `shared_publications` tables and adding `source_type`, `source_ref`, `harvest_meta`, `review_state`, `shared_publication_id` columns to `success_patterns`, `failure_patterns`, `project_rules` (where missing). Backfill `source_type='manual'` and `review_state='confirmed'` for existing rows.
2. Implement `vibecode/db/audit_log_repository.py` (`AuditLogRepository`) with `record(actor, action, target_type, target_id, project_path, meta)` and query helpers.
3. Wire `AuditLogRepository.record(...)` into every existing capture, search, inject, observe code path.
4. Extend `vibecode/core/security.py` redaction with MongoDB SRV URIs, Slack `xoxb-`, JWT `eyJhbGci…`, AWS session tokens. Apply to all captured text fields, not only code.
5. Add Pydantic length limits and path-traversal validators per `Build_Packet_6_7_Unified.md` Section 9, Phase 0.

Tests required (must all pass):
- tests/test_audit_log_repository.py
- tests/test_secret_redaction.py (extend existing)
- tests/test_schema_limits.py
- tests/test_path_traversal.py
- alembic upgrade head and downgrade -1 succeed in CI.

Exit criteria:
- `pytest` green on Windows and Linux.
- `vibecode doctor` shows no new warnings.
- Every captured/searched/injected call results in exactly one `audit_log` row.

Do not touch harvester or Pro databank code in this phase.
~~~

### 13.1 Phase 1 Prompt - Harvester MVP

~~~text
Implement Phase 1 of `Docs/Build_Packet_6_7_Unified.md`: the Knowledge Harvester MVP.

Deliverables:
1. New package `vibecode/harvest/` with:
   - `walker.py` (DocSourceWalker; honors .gitignore, new .vibecodeignore, size cap, max_files, project allowlist).
   - `extractors/claude_md.py` (ClaudeMdExtractor).
   - `extractors/markdown_rule.py` (MarkdownRuleExtractor; imperative-verb rules + pitfall blocks with Fix siblings).
   - `normalizer.py` (CandidateMemory dataclass + content_hash normalization).
   - `dedupe.py` (exact-hash dedupe; embedding hook stubbed).
   - `confidence.py` (formula in Section 7.4).
   - `service.py` (KnowledgeHarvester orchestrator + JSON report writer to `.vibecode/harvest_report.json`).
2. New routes in `vibecode/api/routes_harvest.py`: POST /harvest/scan, POST /harvest/preview, GET /harvest/report.
3. CLI in `vibecode/cli/harvest.py`: `vibecode harvest scan|preview|report|sources`.
4. All harvested writes go through the existing review queue and write an `audit_log` row with `actor="harvester"`.

Tests required (must all pass): see Section 10.2 of the spec. Include fixture files under `tests/fixtures/harvest/`.

Exit criteria:
- Running `vibecode harvest scan --project D:/Vibecoder` produces ≥ 20 candidates with no duplicates on re-run.
- All writes audited; no captured text contains unredacted secrets.
- `pytest` green.

Do not implement ADR / Changelog / Linter / InlineComment extractors yet — those are Phase 2.
~~~

### 13.2 Phase 2 Prompt - Harvester Full Coverage + Extension UX

~~~text
Implement Phase 2 of `Docs/Build_Packet_6_7_Unified.md`.

Backend:
1. Add `vibecode/harvest/extractors/adr.py`, `changelog.py`, `linter_config.py`, `inline_comment.py`. Heuristics in spec Section 7.3.
2. Implement embedding-based near-dup detection in `dedupe.py` guarded behind `EmbeddingService.is_available()`; threshold 0.92.

Extension:
1. New command `VibeCode: Harvest Project Knowledge` in `vibe-code-extension/src/commands/harvestCommand.ts`.
2. First-run prompt on activation when `harvest.runOnInit` is true and CLAUDE.md / AGENTS.md / docs/adr/ exists.
3. Sidebar review group `Harvested (Pending)` with bulk-confirm action.
4. Post-scan webview summary (counts by extractor + top 10 high-confidence items + link to report path).
5. Settings declared in `package.json` as per Section 7.9.

Tests: Section 10.3 of the spec.

Exit criteria:
- Scanning a repo containing CHANGELOG.md, docs/adr/*, .eslintrc, and a CLAUDE.md produces correctly typed items for each extractor.
- mocha tests green in the extension.
- Manual smoke on the Vibecoder workspace: first-run prompt fires, webview opens, bulk-confirm flips state.
~~~

### 13.3 Phase 3 Prompt - Pro Databank Server

~~~text
Implement Phase 3 of `Docs/Build_Packet_6_7_Unified.md`: the Pro Databank server.

Authoritative spec for endpoints, headers, envelopes, and schemas: `Docs/Build_Packet_6_Pro_Shared_Databank.md` Sections 5–6, plus deltas in `Docs/Build_Packet_6_7_Unified.md` Section 8.

Deliverables:
1. New service under `server/pro/` (FastAPI app, separate from the local VibeCode service).
2. Endpoints: POST /databank/contributions, POST /databank/search, POST /databank/feedback, GET /databank/contributions/{id}, POST /databank/retract, plus moderation endpoints in Packet 6 spec.
3. Postgres + pgvector schema migrations.
4. Embedding ingestion worker (sentence-transformers or pluggable provider) writing to the vector column.
5. Moderation queue with SLA timers and audit fields.
6. Docker compose service for the Pro server + Postgres + pgvector.

Tests: Section 10.4 of the unified spec. Use a fake Pro token fixture. Mark network/Postgres tests with `@pytest.mark.pro_server`.

Exit criteria:
- End-to-end: contribute → moderate(approve) → search → retract round-trips against `docker compose up pro`.
- pgvector nearest-neighbor query returns expected order.
- All endpoints respond with the unified envelope (Section 5 of Packet 6).
~~~

### 13.4 Phase 4 Prompt - Pro Sync Adapter (client)

~~~text
Implement Phase 4 of `Docs/Build_Packet_6_7_Unified.md`.

Backend:
1. `vibecode/integrations/pro_sync.py` with `submit`, `search`, `feedback`, `retract`. Use httpx; honor `vibeCode.pro.endpoint` and bearer token from secret storage.
2. Merge logic in `vibecode/core/injection_service.py`: when Pro enabled, fetch team + global results in parallel with local search, then merge with `local_first_boost = 0.25` added to local scores before rerank. Local-first invariant: if local has any result above its rerank floor, it must occupy slot 1.
3. CLI: `vibecode pro share <pattern_id>`, `vibecode pro retract <pattern_id>`, `vibecode pro status`.

Extension:
1. Per-item action "Share to databank" in the review queue, gated to `review_state=confirmed` items only.
2. Settings `vibeCode.pro.enabled`, `vibeCode.pro.scopes`, `vibeCode.pro.endpoint`. Token stored via `vscode.SecretStorage`.

Tests: Section 10.5 of the unified spec.

Exit criteria:
- Sharing a confirmed harvested rule round-trips end-to-end against the Phase 3 Docker stack.
- `inject_context` returns merged results with local-first ordering in a scripted scenario; no regression on Packet 5 fixtures.
- No item is ever published without an explicit user action.
~~~

### 13.5 Phase 5 Prompt - Telemetry, Hardening, Final Report

~~~text
Implement Phase 5 of `Docs/Build_Packet_6_7_Unified.md`.

1. Extend `vibecode/services/token_service.py` and the `/token-report` route to return savings split into buckets `local`, `harvested`, `shared_team`, `shared_global`, sourced from `audit_log`.
2. Add per-endpoint rate limiting middleware (token bucket) for capture, inject, search, observe, harvest with limits in spec Section 9 Phase 5 (re-use existing pre_edit_check limit semantics).
3. Background job `vibecode/jobs/confidence_decay.py` running every 6h, applying the existing decay formula to all patterns.
4. Extend `vibecode doctor` with rows for harvester and Pro health.
5. Generate the final report at `Docs/reports/Packet_6_7_Final_Report.md` using the template in Section 12.

Tests: Section 10.6 of the unified spec.

Exit criteria:
- All Section 11 acceptance criteria pass.
- Final report committed with acceptance matrix fully populated.
- p95 latency for `inject_context` within 10% of the Packet 5 baseline recorded in the report.
~~~

---

## 14. Build Order Cheat-Sheet

1. Phase 0 → merge.
2. Phase 1 → merge.
3. Phase 2 → merge.
4. Phase 3 → merge (server can run in parallel with Phase 4 dev, but Phase 4 depends on Phase 3's contract).
5. Phase 4 → merge.
6. Phase 5 → merge + tag release `v0.6.0-pro`.

---

## 15. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Harvester floods review queue with low-value items | Confidence threshold + per-extractor caps + bulk-confirm/discard UX |
| Shared databank leaks proprietary info | Mandatory redaction + pii_risk_score gate + per-item opt-in + retract endpoint |
| Local-first invariant regresses under merge | Contract test `test_injection_merge.py` enforces slot 1 = local when local has any result |
| Pro server outage hurts agent UX | Pro calls are best-effort with 750ms hard timeout; local results are returned regardless |
| Auto-confirm too aggressive | Default 0.8, configurable, every auto-confirm still writes audit log and is retractable |

---

## 16. Packet 8 Candidates — Mid-Task Auto-Retrieval

Discovered during a 2026-05-17 dogfooding session where the agent rediscovered the same captured PowerShell-quoting failure (`abc9ec56`) three times in one conversation despite the pattern already being in the KB. Root cause: captured rules only help if the agent re-queries the KB between sub-steps, but Packet 5's auto-installed agent rules only nudge `vibecode_inject_context` at task start, not mid-task.

### 16.1 Auto-inject on tool-call error

**Behavior.** When the VS Code extension observes a non-zero exit from a terminal command, or the MCP client reports a tool error, automatically issue a `vibecode_search_memory` call keyed on the failing command + the first 120 chars of stderr, and surface any matching failure patterns inline (toast, sidebar highlight, or appended to the next agent prompt via the MCP context channel).

**Acceptance.**
- A configurable threshold (default: any exit ≥ 1 from a tracked terminal) triggers the search.
- Search uses both the command tokens and the stderr fragment; results are deduped against the current session's already-shown warnings.
- If at least one pattern matches with score above `vibeCode.autoRecall.minScore` (default 0.5), inject it into the agent context channel (MCP `notify` or extension chat participant injection) within 500 ms of the error.
- Audit log entry: `auto_recall_on_error` with command, stderr hash, returned pattern ids.
- Opt-out setting `vibeCode.autoRecall.onTerminalError` (default `true`).

**Why it ships in Packet 8 not 6/7.** Requires hooks into the agent's context channel that today only exist for Copilot Chat; Cursor and Windsurf integrations land in Packet 7, so Packet 8 is the earliest layer all four supported clients have the surface.

### 16.2 Pre-flight scan on agent-authored terminal commands

**Behavior.** When the extension's edit-observation loop (Packet 5 §4) sees an agent-issued `run_in_terminal` call, scan the proposed command for known antipatterns from the local KB (e.g. `\"` inside `git commit -m`, `--query`-like substrings inside `-m`, native-exe calls with embedded `"`), and either (a) annotate the chat with a warning before execution, or (b) if confidence ≥ 0.9, block-and-suggest with a one-click rewrite.

**Acceptance.**
- A new `vibecode pre_command_check` MCP tool accepts `{command, shell, cwd}` and returns matching failure patterns + suggested rewrite.
- The VS Code extension wires this tool to the agent's terminal-tool surface where the API permits (Copilot Chat: chat participant pre-hook; MCP: prompt-prefix injection).
- Test fixture: feed the PowerShell `\"` antipattern and verify the warning surfaces before execution.
- Audit log entry: `pre_command_check` with command hash, returned pattern ids, agent action (proceeded / cancelled / rewrote).

**Out of scope for Packet 8.** Auto-rewrite without user approval. The check is advisory; the user (or agent) must still confirm.

### 16.3 Empirical motivation

In a single session, the captured PowerShell-quoting pattern would have saved an estimated **~9,000 tokens** if mid-task auto-recall had fired on the first two relapses. Aggregated across the 7 patterns captured this session, mid-task recall would have prevented an estimated **~12,000 of the ~15,200 wasted tokens** (the remaining ~3,000 are first-encounter discovery costs that no recall could avoid).

---

End of unified packet.
