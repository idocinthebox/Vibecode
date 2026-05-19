# Packet 8 Execution Report (2026-05-18)

## Scope
Implemented Build Packet 8 fixes across local service, Pro server, shared service logic, extension integration, and tests.

## What Changed
- Wired confidence decay startup in `vibecode/api/app.py` and corrected run-then-sleep ordering in `vibecode/jobs/confidence_decay.py`.
- Added `data_dir` setting in `vibecode/config/settings.py`.
- Hardened Pro server with bearer auth dependency (`server/pro/security.py`), contribution redaction+size cap, and global Pro rate limiting.
- Added escalated moderation state and migration helper in `server/pro/db/schema.py`; moderation now sets `escalated` correctly.
- Added FTS5 search index/triggers and switched Pro search to `MATCH`.
- Hardened `vibecode/core/memory_service.py` Pro flows:
  - explicit allow-list projection for `pro_share`
  - redaction on shared string fields
  - project allowlist enforcement for share payloads
  - stable `PRO_REQUEST_FAILED` error envelope for share/retract/status/search
- Updated `vibecode/api/routes_pro.py` to pass `project_path` to `pro_share`.
- Added `/memory/recent` route in `vibecode/api/routes_memory.py` and backend implementation in `vibecode/core/memory_service.py`.
- Improved `vibecode/api/middleware.py` with empty-window eviction, `Retry-After`/rate headers, and XFF-ignore behavior.
- Improved `vibecode/services/injection_service.py` merge dedup key and Pro-unavailable markdown note.
- Added doctor service-version drift check in `vibecode/cli/commands_doctor.py`.
- Extension updates:
  - `terminalRecallService` now captures real command output tails via shell integration stream
  - `shareToDatabank` now uses recent-memory QuickPick and sends `project_path`
  - `apiClient` + API types updated for recent-memory and share payload support
- Added release graph helper script `scripts/build_release_graph.ps1` and README release checklist note.
- Fixed pre-existing syntax break in `vibe-code-extension/src/services/rulesInstallerService.ts` to restore extension compile.

## Validation
- Targeted backend validation:
  - `python -m pytest tests/test_decay_scheduler_startup.py tests/databank tests/test_rate_limit_middleware.py tests/test_injection_merge.py tests/test_pro_sync_adapter.py tests/test_doctor_version_drift.py -q`
  - Result: **34 passed** (2 FastAPI deprecation warnings for `on_event`).
- Extension validation:
  - `npm run compile`
  - `npm test`
  - Result: compile succeeded, extension tests passed (**49 passing**).
- Full Python suite:
  - `python -m pytest -q`
  - Result: blocked during collection by environment mismatch (`numpy` wheel mismatch: cp313 artifact in cp312 env for postgres tests).

## Runtime Endpoint Check
- Service had stale-process port conflicts on 8765; after killing listener and restarting from venv, OpenAPI includes:
  - `/pro/share/{memory_type}/{memory_id}`
  - `/memory/check-command`
  - `/reports/tokens/buckets`
  - `/memory/recall-on-error`
  - `/memory/recent`

## Commits
- No commit created in this execution window.

## Follow-ups
- Resolve Python environment mismatch for postgres suite (`numpy` binary compatibility in `.venv`).
- If desired, migrate FastAPI startup hook from deprecated `@app.on_event("startup")` to lifespan handlers.
- Optional: run/repair extension lint (`npm run lint`) where unrelated pre-existing no-unused-vars issues remain.
