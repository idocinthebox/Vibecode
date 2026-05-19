# Known Issues / Latent Bugs

Operational gaps discovered during dogfooding. These are real bugs, not
hot-patch artifacts. Fix priority is for product polish before any beta hand-off.

---

## 1. `vibecode service stop` is best-effort and does not stop the service

**Symptom**

```text
PS> vibecode service stop
⚠ Service stop is best-effort. Use Ctrl+C if running in foreground.
```

The uvicorn process keeps running and the port stays bound. From a different
shell context, `Stop-Process -Id <pid> -Force` fails with **Access is denied**
on Windows, so the user is left with no in-band way to shut the daemon down
short of Task Manager or reboot.

**Root cause**

`service start` does not record a PID file, and `service stop` has no PID to
target. The command is essentially a no-op disguised as an action.

**Suggested fix**

- On `service start`, write `~/.vibecode/service.pid` (and `service.port`).
- On `service stop`, read the PID file and:
  - POSIX: `os.kill(pid, signal.SIGTERM)` then wait + `SIGKILL` fallback.
  - Windows: `subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"])`.
- Remove the PID file on graceful shutdown (FastAPI shutdown event).
- If no PID file exists, fall back to scanning the configured port and refuse
  to "stop" silently — print a clear "no managed service found" message.

---

## 2. No process tracking / no detached start

`vibecode service start` runs uvicorn in the foreground of the launching
terminal. Closing that terminal kills the service. There is no
`service start --detach` and no Windows-service / systemd wrapper.

Combined with #1, this means the only reliable way to run VibeCode today is
to dedicate a terminal to it and never close that window.

**Suggested fix**

- Add `vibecode service start --detach` that spawns the uvicorn process via
  `subprocess.Popen(..., creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)`
  on Windows and `start_new_session=True` on POSIX, then writes the PID file
  from #1 and exits.
- Document an optional `nssm`/`sc.exe` recipe for installing as a real
  Windows service for users who want it.

---

## 3. No on-disk service logs

Uvicorn logs to stdout. When the launching terminal is gone, the logs are
gone with it. During this session a stale process began returning **HTTP 500
from `/health`** while still bound to port 8765, and we could not determine
the cause because no stack trace was preserved.

**Suggested fix**

- Configure uvicorn with `log_config` writing to
  `~/.vibecode/logs/service.log` (rotating, e.g. 5 × 5 MB).
- Keep stdout logging too when running in foreground.
- Add `vibecode service logs [--tail N] [--follow]` for convenience.

---

## 4. `/health` can return 500 on long-lived processes (root cause unknown)

**Symptom** A service process that started fine and was answering requests
eventually begins returning `HTTP 500 Internal Server Error` from `/health`
while `Get-NetTCPConnection` confirms it is still listening on 8765. A fresh
restart of the same code returns 200 immediately.

**Status** Root cause unidentified — we had no logs (see #3). Plausible
candidates to investigate once logs exist:

- Stale SQLite connection after long idle (need to verify
  `VibeCodeService` uses short-lived sessions / `SessionLocal` per request,
  not a process-wide handle).
- Cached schema metadata in a long-lived `VibeCodeService` instance becoming
  inconsistent after a migration or an external write.
- An exception in the response-model serialization that only triggers under
  certain DB states (the route uses `response_model=HealthResponse`, so a
  field-shape mismatch surfaces as 500).

**Action** Land #3 first, then reproduce. Until then, document the
workaround: kill the stale PID and restart.

---

## Operator workaround (until #1–#3 land)

1. Find the listener: `Get-NetTCPConnection -LocalPort 8765 -State Listen | Select OwningProcess`
2. Kill it (may require admin on Windows): `Stop-Process -Id <pid> -Force`
3. Restart from the repo root with the venv active:

   ```powershell
   cd d:\Vibecoder
   .\.venv\Scripts\Activate.ps1
   vibecode service start
   ```

4. Verify: `Invoke-WebRequest http://127.0.0.1:8765/health -UseBasicParsing`
   should return `HTTP 200` and a JSON status body.

The VS Code extension's status bar polls `/health` and will flip from
**Vibecode disconnected** to **Vibecode connected** within a few seconds of
the fresh process accepting requests.
