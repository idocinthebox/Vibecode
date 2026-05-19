# Build Packet 8 — Packet 6/7 Hardening & Fixes

**Status:** Ready for Codex
**Source review:** [Docs/reports/Packet_6_7_Code_Review.md](Docs/reports/Packet_6_7_Code_Review.md)
**Vibecoder failure_id (decay scheduler):** `90f76e3f-641b-473b-9f61-59a99a2a7cf2`
**Branch convention:** `packet-8-fixes`
**Mandatory workflow:** Follow `.github/copilot-instructions.md` — call `vibecode_inject_context` before each step, `vibecode_capture_failure` on every test failure, `vibecode_capture_success` after each green test.

---

## 0. Pre-flight (5 min)

```powershell
Set-Location D:\Vibecoder
git checkout -b packet-8-fixes
.\.venv\Scripts\python.exe -m pip install -e . --quiet
.\.venv\Scripts\python.exe -m pytest -q   # baseline; should be ≤ current green count
```

If service is running: `vibecode service stop` then `vibecode service start` after Step 1 so it picks up the new startup hook.

---

## 1. CRITICAL — Wire the confidence-decay scheduler at app startup

**File:** [vibecode/api/app.py](vibecode/api/app.py)

Currently `start_decay_scheduler` is dead code. Wire it via a FastAPI startup event so the daemon thread starts when the local service boots.

### 1.1 Edit `create_app()`

Add imports at the top:

```python
from pathlib import Path
from vibecode.jobs.confidence_decay import start_decay_scheduler, run_once
from vibecode.db.sqlite_connection import get_default_base_dir  # whatever helper exists; see step 1.3
```

Inside `create_app()` after the routers are registered, append:

```python
@app.on_event("startup")
def _start_background_jobs() -> None:
    base_dir = Path(settings.data_dir) if getattr(settings, "data_dir", None) else get_default_base_dir()
    # Eager first pass so decay does not wait the full interval after a cold start.
    run_once(base_dir)
    start_decay_scheduler(base_dir, interval_hours=settings.confidence_decay_interval_hours)
```

If `settings.data_dir` does not exist, add it in step 1.3.

### 1.2 Fix `_decay_loop` to run-then-sleep

**File:** [vibecode/jobs/confidence_decay.py](vibecode/jobs/confidence_decay.py)

Replace the body of `_decay_loop` with:

```python
def _decay_loop(base_dir: Path, interval_seconds: int) -> None:
    while True:
        try:
            run_once(base_dir)
        except Exception as exc:  # pragma: no cover
            logger.warning("Unhandled error in decay loop: %s", exc)
        time.sleep(interval_seconds)
```

### 1.3 Add a `data_dir` setting if missing

**File:** [vibecode/config/settings.py](vibecode/config/settings.py)

Add (only if `data_dir` is not already defined elsewhere):

```python
data_dir: str = ""   # empty → use default per-user store
```

### 1.4 Tests

**New file:** `tests/test_decay_scheduler_startup.py`

```python
from unittest.mock import patch
from fastapi.testclient import TestClient

def test_startup_starts_decay_scheduler(tmp_path, monkeypatch):
    monkeypatch.setenv("VIBECODE_DATA_DIR", str(tmp_path))
    with patch("vibecode.api.app.start_decay_scheduler") as start, \
         patch("vibecode.api.app.run_once") as eager:
        from vibecode.api.app import create_app
        with TestClient(create_app()):
            pass
        start.assert_called_once()
        eager.assert_called_once()
```

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_decay_scheduler_startup.py -q
```

On green: capture success with `task_intent="wire packet 6/7 confidence decay scheduler"`.

---

## 2. CRITICAL — Lock down the Pro server (auth + redaction + rate limit + size cap)

### 2.1 Bearer-token auth dependency

**New file:** `server/pro/security.py`

```python
"""Shared Pro-server auth dependency."""
import os
from fastapi import Header, HTTPException, status

def require_bearer(authorization: str | None = Header(default=None)) -> str:
    expected = os.environ.get("PRO_API_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=503, detail="Pro server token not configured")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if token != expected:
        raise HTTPException(status_code=403, detail="Invalid bearer token")
    return token
```

Wire it into every Pro route module:

**Files:** [server/pro/routes/contributions.py](server/pro/routes/contributions.py), [server/pro/routes/search.py](server/pro/routes/search.py), [server/pro/routes/moderation.py](server/pro/routes/moderation.py)

Replace each `router = APIRouter()` line with:

```python
from server.pro.security import require_bearer
router = APIRouter(dependencies=[Depends(require_bearer)])
```

(`Depends` is already imported in each file.)

### 2.2 Server-side secret redaction + size cap on submissions

**File:** [server/pro/routes/contributions.py](server/pro/routes/contributions.py) — `submit_contribution()`

```python
from vibecode.utils.secret_redaction import redact_secrets

MAX_BODY_BYTES = 64 * 1024

def _redact_data(data: dict) -> dict:
    out = {}
    for k, v in data.items():
        out[k] = redact_secrets(v) if isinstance(v, str) else v
    return out

# inside submit_contribution, before building title/summary:
data = _redact_data(request.data)
body_json = __import__("json").dumps(data)
if len(body_json.encode("utf-8")) > MAX_BODY_BYTES:
    raise HTTPException(status_code=413, detail="Submission too large")
```

### 2.3 Per-IP rate limit on contributions

Reuse `vibecode.api.middleware.RateLimitMiddleware`. In [server/pro/main.py](server/pro/main.py):

```python
from vibecode.api.middleware import RateLimitMiddleware

def create_pro_app(data_dir=None) -> FastAPI:
    ...
    app.add_middleware(RateLimitMiddleware, default_per_min=60, pre_edit_check_per_min=60)
    ...
```

### 2.4 Tests

Update [tests/databank/test_contributions.py](tests/databank/test_contributions.py), [tests/databank/test_search.py](tests/databank/test_search.py), [tests/databank/test_moderation.py](tests/databank/test_moderation.py):

- Set `PRO_API_TOKEN=test-token` via `monkeypatch.setenv` in the fixture that builds the app.
- Pass `headers={"Authorization": "Bearer test-token"}` on every request.
- Add 3 negative tests in a new `tests/databank/test_auth.py`: missing header → 401, wrong token → 403, missing env → 503.
- Add 1 redaction test: POST a contribution whose `data["failure_reason"]` contains `sk_live_abc123…`; assert stored row's `body_json` does not contain `sk_live_`.
- Add 1 size-cap test: POST `data={"x":"a"*70000}` → 413.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/databank -q
```

---

## 3. HIGH — Redact and allowlist `pro_share`

**File:** [vibecode/core/memory_service.py](vibecode/core/memory_service.py) — `pro_share`

### 3.1 Switch to an explicit allow-list and redact strings

Replace each `data = { k: v for k, v in dict(row).items() if k not in (...) }` block with:

```python
SHARE_ALLOW_LIST_FAILURE = (
    "failure_id", "task_intent", "bad_suggestion", "failure_reason",
    "prevention_rule", "corrected_approach", "language", "framework", "severity",
)
SHARE_ALLOW_LIST_SUCCESS = (
    "pattern_id", "name", "intent_description", "language", "framework",
    "reasoning_summary",
)

def _project_row(row, allow):
    d = {}
    for k in allow:
        v = row[k] if k in row.keys() else ""
        d[k] = redact_secrets(v) if isinstance(v, str) else v
    return d

# inside pro_share:
if memory_type == "failure_pattern":
    data = _project_row(row, SHARE_ALLOW_LIST_FAILURE)
elif memory_type == "success_pattern":
    data = _project_row(row, SHARE_ALLOW_LIST_SUCCESS)
```

### 3.2 Enforce project allowlist on share

Add a `project_path` parameter to `pro_share`:

```python
def pro_share(self, memory_type: str, memory_id: str, project_path: str | None = None) -> dict[str, Any]:
    if project_path is not None and not self._project_allowed(project_path):
        return self._error("PROJECT_NOT_ALLOWED", project_path=project_path)
    ...
```

**File:** [vibecode/api/routes_pro.py](vibecode/api/routes_pro.py) — `pro_share`

```python
def pro_share(memory_type, memory_id, request: ProShareRequest, service=Depends(get_service)):
    return service.pro_share(memory_type=memory_type, memory_id=memory_id,
                             project_path=request.project_path or None)
```

### 3.3 Tests

Append to existing `tests/test_pro_sync_adapter.py` (or new `tests/test_pro_share.py`):

```python
def test_pro_share_redacts_secrets(...):  # seed failure pattern with 'sk_live_xxx' in failure_reason; submit; assert adapter received redacted text
def test_pro_share_rejects_disallowed_project(...):  # disallowed project_path → {"error":"PROJECT_NOT_ALLOWED"}
def test_pro_share_uses_allowlist(...):  # confirm content_hash/is_active never reach the adapter payload
```

---

## 4. HIGH — Capture real terminal output in `TerminalRecallService`

**File:** [vibe-code-extension/src/services/terminalRecallService.ts](vibe-code-extension/src/services/terminalRecallService.ts)

Use the Shell Integration `execution.read()` async iterable to grab the last ~4 KB of output. Fall back to the command line only if `read` is unavailable.

```ts
private async _captureTail(execution: any, maxBytes = 4096): Promise<string> {
  if (typeof execution?.read !== 'function') return '';
  let buf = '';
  try {
    for await (const chunk of execution.read()) {
      buf += typeof chunk === 'string' ? chunk : Buffer.from(chunk).toString('utf8');
      if (buf.length > maxBytes * 4) buf = buf.slice(-maxBytes * 2);
    }
  } catch { /* ignore */ }
  // strip ANSI
  return buf.replace(/\x1B\[[0-?]*[ -/]*[@-~]/g, '').slice(-maxBytes);
}
```

In the event handler:

```ts
this.disposable = eventApi(async (e) => {
  const exitCode = e.exitCode ?? 0;
  if (exitCode === 0) return;
  const cfg = this.getConfig();
  if (!cfg.get<boolean>('autoRecall.enabled', true)) return;

  const command = e.execution?.commandLine?.value ?? '';
  const tail = await this._captureTail(e.execution);
  const errorOutput = tail || `Command failed: ${command}`;
  const projectPath = this.workspaceFolders()?.[0]?.uri?.fsPath;
  this._recallForError(errorOutput, command, projectPath).catch(() => {});
});

private async _recallForError(errorOutput: string, command: string, projectPath: string | undefined) {
  const result = await this.api.autoRecallOnError({ error_output: errorOutput, project_path: projectPath, command });
  ...
}
```

(No new dependency.) Update `tsconfig` `lib` if `for await` complains.

### Test

Add `vibe-code-extension/test/suite/terminalRecallService.test.ts` that fakes an `execution` object exposing `read()` as an async generator yielding `"ENOENT: file not found"` and asserts `_captureTail` returns that string.

---

## 5. HIGH — Pro moderation: add `escalated` state

**File:** [server/pro/db/schema.py](server/pro/db/schema.py)

Update the CHECK constraint:

```sql
review_state TEXT NOT NULL DEFAULT 'pending'
  CHECK(review_state IN ('pending','approved','rejected','escalated'))
```

Add a migration helper (since CHECK changes require table rebuild in SQLite, use a guarded `try/except` on existing data):

```python
def _ensure_escalated_state(conn):
    cur = conn.execute("PRAGMA table_info(databank_patterns)")
    cols = [r[1] for r in cur.fetchall()]
    if "review_state" not in cols:
        return
    # Rebuild only if CHECK is missing 'escalated'.
    try:
        conn.execute("UPDATE databank_patterns SET review_state='escalated' WHERE 0")
        conn.commit()
    except sqlite3.IntegrityError:
        conn.executescript("""
            ALTER TABLE databank_patterns RENAME TO _old_patterns;
            -- recreate with new CHECK using PRO_SCHEMA_SQL above
            -- (use CREATE TABLE…AS SELECT, then INSERT to copy data; drop _old_patterns)
        """)
```

Call `_ensure_escalated_state(conn)` from `get_pro_connection` after `executescript(PRO_SCHEMA_SQL)`.

**File:** [server/pro/routes/moderation.py](server/pro/routes/moderation.py)

```python
new_state = {"approve": "approved", "reject": "rejected", "escalate": "escalated"}[action]
```

And exclude `escalated` from the default queue:

```sql
WHERE is_active = 1 AND review_state IN ('pending')
```

### Test

Update [tests/databank/test_moderation.py](tests/databank/test_moderation.py): after escalate, assert state is `escalated` and that item no longer appears in `/databank/moderation/queue`.

---

## 6. HIGH — Service version mismatch warning in `vibecode doctor`

**File:** [vibecode/cli/commands_doctor.py](vibecode/cli/commands_doctor.py)

Bump app version in [vibecode/api/app.py](vibecode/api/app.py) to match `vibecode.__version__`:

```python
from vibecode import __version__
app = FastAPI(title="VibeCode Local Service", version=__version__, ...)
```

Then in doctor, hit `/openapi.json`, parse `info.version`, compare with `vibecode.__version__`. Emit `WARNING: Running service is older than installed package — run 'vibecode service restart'.` when they differ.

### Test

Add `tests/test_doctor_version_drift.py` with a stubbed httpx client returning `info.version="0.3.0"` while `vibecode.__version__="0.4.0"`; assert the warning line is printed.

---

## 7. MEDIUM — `RateLimitMiddleware` hardening

**File:** [vibecode/api/middleware.py](vibecode/api/middleware.py)

1. Drop empty deques after eviction:
   ```python
   if not window:
       self._windows.pop(window_key, None)
   ```
2. Add `Retry-After: 60` and informative headers on 429:
   ```python
   headers = [
       [b"content-type", b"application/json"],
       [b"content-length", str(len(body)).encode()],
       [b"retry-after", b"60"],
       [b"x-ratelimit-limit", str(limit).encode()],
       [b"x-ratelimit-remaining", b"0"],
   ]
   ```
3. Ignore `X-Forwarded-For` entirely for bucket keying (keep only `scope["client"][0]`). Comment the header lookup out / remove it.

### Test

Update existing rate-limit test to assert presence of `Retry-After` header on the 429 response and that XFF spoofing no longer creates a new bucket.

---

## 8. MEDIUM — Injection merge improvements

**File:** [vibecode/services/injection_service.py](vibecode/services/injection_service.py)

1. Dedup key on `(memory_type, title.lower(), language)`:
   ```python
   key = (r.result_type, r.title.strip().lower(), getattr(r.obj, "language", ""))
   ```
2. When `_search_remote` returns an error, append an injected note:
   ```python
   # Inside inject(), after computing results:
   if remote_results == [] and self._last_remote_error:
       lines.append("## Pro Databank Unavailable")
       lines.append(f"- *Note:* {self._last_remote_error}")
       lines.append("")
   ```
   Store `self._last_remote_error` from `_search_remote` when payload contains `"error"`.

### Test

Add `tests/test_injection_merge.py` cases: (a) two local items with same title but different language are both retained; (b) Pro error surfaces in the markdown.

---

## 9. MEDIUM — Stable error envelope on Pro endpoints

**File:** [vibecode/core/memory_service.py](vibecode/core/memory_service.py)

In `pro_share`, `pro_retract`, `pro_status`, `pro_search` — instead of returning `{"error": str(exc)}` from the adapter directly, map all errors to `_error("PRO_REQUEST_FAILED")` and log the real message:

```python
PRO_REQUEST_FAILED = "PRO_REQUEST_FAILED"
# Add to _error messages dict:
"PRO_REQUEST_FAILED": ("Pro databank request failed.", "Check service logs and 'vibecode doctor'."),
```

Adjust the call sites accordingly.

### Test

Update `tests/test_pro_sync_adapter.py`: when adapter raises, route returns `{"error":"PRO_REQUEST_FAILED",...}`, never the raw exception string.

---

## 10. LOW — Pro search FTS5 index (optional but recommended)

**File:** [server/pro/db/schema.py](server/pro/db/schema.py)

Append:

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS databank_patterns_fts USING fts5(
    title, summary, language, framework, content='databank_patterns', content_rowid='rowid'
);
CREATE TRIGGER IF NOT EXISTS databank_patterns_ai AFTER INSERT ON databank_patterns BEGIN
  INSERT INTO databank_patterns_fts(rowid, title, summary, language, framework)
  VALUES (new.rowid, new.title, new.summary, new.language, new.framework);
END;
CREATE TRIGGER IF NOT EXISTS databank_patterns_ad AFTER DELETE ON databank_patterns BEGIN
  INSERT INTO databank_patterns_fts(databank_patterns_fts, rowid, title, summary, language, framework)
  VALUES('delete', old.rowid, old.title, old.summary, old.language, old.framework);
END;
CREATE TRIGGER IF NOT EXISTS databank_patterns_au AFTER UPDATE ON databank_patterns BEGIN
  INSERT INTO databank_patterns_fts(databank_patterns_fts, rowid, title, summary, language, framework)
  VALUES('delete', old.rowid, old.title, old.summary, old.language, old.framework);
  INSERT INTO databank_patterns_fts(rowid, title, summary, language, framework)
  VALUES (new.rowid, new.title, new.summary, new.language, new.framework);
END;
```

Rewrite `search_databank` to use `MATCH`:

```python
sql_terms = " ".join(f'"{t}"' for t in terms)
rows = conn.execute("""
  SELECT p.* FROM databank_patterns p
  JOIN databank_patterns_fts f ON f.rowid = p.rowid
  WHERE f MATCH ? AND p.is_active=1 AND p.review_state='approved'
  ORDER BY rank LIMIT ?
""", (sql_terms, request.max_results)).fetchall()
```

### Test

Update [tests/databank/test_search.py](tests/databank/test_search.py) to assert ordering by rank (insert decoy + match item, assert match wins).

---

## 11. LOW — `shareToDatabankCommand` UX

**File:** [vibe-code-extension/src/commands/shareToDatabankCommand.ts](vibe-code-extension/src/commands/shareToDatabankCommand.ts)

Replace `showInputBox` for `memoryId` with a `showQuickPick` populated from a new API call `GET /memory/recent?type={memoryType}&limit=25` (add this lightweight route in [vibecode/api/routes_memory.py](vibecode/api/routes_memory.py); selects `(id, title, source_type)`).

Keep the manual paste as a "Type ID…" item at the bottom.

---

## 12. LOW — Rebuild graph as part of release

**File:** new `scripts/build_release_graph.ps1`

```powershell
Set-Location $PSScriptRoot\..
.\.venv\Scripts\graphify.exe vscode-build .
git add graphify-out/graph.json graphify-out/metadata.json
git commit -m "chore: refresh graphify graph"
```

Mention in [README.md](README.md) "Release checklist: run `scripts/build_release_graph.ps1` before tagging".

---

## 13. Final validation

```powershell
.\.venv\Scripts\python.exe -m pytest -q
cd vibe-code-extension; npm run lint; npm run compile; npm test; cd ..
vibecode service stop; vibecode service start
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/openapi.json |
  Select-Object -ExpandProperty Content |
  Select-String -Pattern "/pro/share|/memory/check-command|/reports/tokens/buckets|/memory/recall-on-error"
```

All four endpoint patterns must appear.

Then:

```powershell
.\.venv\Scripts\graphify.exe vscode-build .
git add .
git commit -m "fix(packet-8): harden pro server, wire decay scheduler, redact share, capture terminal tail"
git push origin packet-8-fixes
```

Open PR; reference review report and Vibecoder failure_id `90f76e3f`.

---

## Acceptance criteria

- [ ] `vibecode service start` → background decay thread present (`threading.enumerate()` shows `vibecode-confidence-decay`).
- [ ] `POST /databank/contributions` without bearer → 401; with bad bearer → 403; with `PRO_API_TOKEN` unset → 503.
- [ ] Submitting a pattern containing `sk_live_xxx` → stored `body_json` has no `sk_live_` substring.
- [ ] `pro_share` rejects disallowed project paths.
- [ ] Auto-recall surfaces patterns matching actual stderr (verified by manual repro: `python -c "raise FileNotFoundError('foo')"`).
- [ ] Escalated patterns leave the moderation queue and appear under a new `escalated` filter.
- [ ] `vibecode doctor` warns when service `info.version` differs from package version.
- [ ] 429 responses include `Retry-After: 60`.
- [ ] Pro databank errors return `{"error":"PRO_REQUEST_FAILED",...}` with no raw exception text.
- [ ] `pytest -q` and extension `npm test` both green.

---

## Out of scope (defer to Packet 9)

- Async httpx migration for `ProSyncAdapter`.
- Per-token Pro rate limits (only per-IP in Packet 8).
- Removing the duplicate `d:\Vibecode\vibe-code-extension\` directory — needs operator confirmation.
- TLS / mTLS on the Pro server.
