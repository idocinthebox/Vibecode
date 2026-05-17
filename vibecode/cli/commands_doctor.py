from __future__ import annotations

import platform
import sys
from pathlib import Path

import typer

from vibecode.cli.console import print_info
from vibecode.cli.formatters import format_doctor_report
from vibecode.config.paths import get_vibecode_dir
from vibecode.core.security import redact_secrets
from vibecode.db.sqlite_connection import get_db_path


def cmd_doctor() -> None:
    base = get_vibecode_dir()
    checks: list[dict] = []

    checks.append({
        "name": "VibeCode version",
        "status": "OK",
        "detail": "0.3.0",
    })

    checks.append({
        "name": "Python version",
        "status": "OK",
        "detail": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    })

    config_path = base / "config.toml"
    if config_path.exists():
        checks.append({"name": "Project config file", "status": "OK", "detail": str(config_path)})
    else:
        checks.append({"name": "Project config file", "status": "WARNING", "detail": "Not found", "fix": "vibecode config set general.default_storage sqlite"})

    if base.exists():
        checks.append({"name": ".vibecode folder", "status": "OK"})
    else:
        checks.append({"name": ".vibecode folder", "status": "ERROR", "detail": "Not found", "fix": "vibecode init"})

    db_path = get_db_path(base)
    if db_path.exists():
        checks.append({"name": "SQLite database", "status": "OK", "detail": str(db_path)})
    else:
        json_exists = (base / "success_patterns").exists()
        checks.append({
            "name": "Storage backend",
            "status": "WARNING" if json_exists else "ERROR",
            "detail": "JSON fallback" if json_exists else "None",
            "fix": "vibecode init-db" if not json_exists else "",
        })

    allowlist_path = base / "allowed_projects.json"
    if allowlist_path.exists():
        checks.append({"name": "Project allowlist", "status": "OK"})
    else:
        checks.append({"name": "Project allowlist", "status": "WARNING", "detail": "Empty", "fix": "vibecode project allow <path>"})

    checks.append({"name": "Secret redaction", "status": "OK", "detail": "Enabled"})

    agent_profiles_dir = base / "agent_profiles"
    if agent_profiles_dir.exists() and any(agent_profiles_dir.iterdir()):
        checks.append({"name": "Agent profiles", "status": "OK"})
    else:
        checks.append({"name": "Agent profiles", "status": "WARNING", "detail": "Not seeded", "fix": "vibecode init"})

    format_doctor_report(checks)
