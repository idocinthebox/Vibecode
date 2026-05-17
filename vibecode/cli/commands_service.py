from __future__ import annotations

import typer

from vibecode.cli.console import print_info, print_success, print_warning
from vibecode.config.paths import get_vibecode_dir
from vibecode.db.sqlite_connection import get_db_path
from vibecode.core.memory_service import VibeCodeService


def cmd_service_start(
    host: str = "127.0.0.1",
    port: int = 8765,
) -> None:
    import uvicorn
    from vibecode.api.app import create_app

    print_info(f"Starting VibeCode service on {host}:{port}")
    uvicorn.run(create_app(), host=host, port=port, log_level="info")


def cmd_service_status() -> None:
    svc = VibeCodeService()
    health = svc.health_check()
    for k, v in health.items():
        print_info(f"{k}: {v}")


def cmd_service_stop() -> None:
    print_warning("Service stop is best-effort. Use Ctrl+C if running in foreground.")


def cmd_service_doctor() -> None:
    base = get_vibecode_dir()
    checks = {
        ".vibecode exists": base.exists(),
        "config.json exists": (base / "config.json").exists(),
        "success_patterns dir": (base / "success_patterns").exists(),
        "failure_patterns dir": (base / "failure_patterns").exists(),
        "project_rules dir": (base / "project_rules").exists(),
        "agent_profiles dir": (base / "agent_profiles").exists(),
        "SQLite DB": get_db_path(base).exists(),
    }
    all_ok = True
    for label, ok in checks.items():
        status = "OK" if ok else "MISSING"
        if ok:
            print_success(f"  [{status}] {label}")
        else:
            print_warning(f"  [{status}] {label}")
            all_ok = False
    if all_ok:
        print_success("All checks passed.")
    else:
        print_warning("Some checks failed. Run 'vibecode init' and 'vibecode init-db'.")
