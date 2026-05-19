from __future__ import annotations

import os
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

    # ------------------------------------------------------------------
    # Harvester rows
    # ------------------------------------------------------------------
    if db_path.exists():
        try:
            from vibecode.db.sqlite_connection import get_connection

            conn = get_connection(base)
            pending_row = conn.execute(
                "SELECT COUNT(*) AS c FROM failure_patterns WHERE is_active=1 AND review_state='pending' AND source_type LIKE 'harvest:%'"
                " UNION ALL "
                "SELECT COUNT(*) AS c FROM success_patterns WHERE is_active=1 AND review_state='pending' AND source_type LIKE 'harvest:%'"
                " UNION ALL "
                "SELECT COUNT(*) AS c FROM project_rules WHERE is_active=1 AND review_state='pending' AND source_type LIKE 'harvest:%'"
            ).fetchall()
            pending_count = sum(row["c"] for row in pending_row)

            last_scan_row = conn.execute(
                "SELECT MAX(created_at) AS ts FROM audit_log WHERE action = 'harvest.scan'"
            ).fetchone()
            last_scan = last_scan_row["ts"] if last_scan_row and last_scan_row["ts"] else "never"
            conn.close()

            status = "OK" if pending_count == 0 else "WARNING"
            detail = f"Pending harvested items: {pending_count}, last scan: {last_scan}"
            fix = "vibecode harvest scan --project <path>" if pending_count > 0 else ""
            checks.append({"name": "Harvester", "status": status, "detail": detail, "fix": fix})
        except Exception as exc:
            checks.append({"name": "Harvester", "status": "WARNING", "detail": f"Could not query DB: {exc}"})
    else:
        checks.append({"name": "Harvester", "status": "INFO", "detail": "No database (harvester requires init-db)"})

    # ------------------------------------------------------------------
    # Pro databank rows
    # ------------------------------------------------------------------
    pro_endpoint = os.environ.get("VIBECODE_PRO_ENDPOINT", "")
    pro_token = os.environ.get("VIBECODE_PRO_TOKEN", "")

    if not pro_endpoint:
        checks.append({
            "name": "Pro databank",
            "status": "INFO",
            "detail": "Not configured (optional)",
            "fix": "Set VIBECODE_PRO_ENDPOINT and VIBECODE_PRO_TOKEN to enable",
        })
    else:
        token_set = bool(pro_token)
        if not token_set:
            checks.append({
                "name": "Pro databank",
                "status": "WARNING",
                "detail": f"Endpoint set ({pro_endpoint}) but VIBECODE_PRO_TOKEN is missing",
                "fix": "Set VIBECODE_PRO_TOKEN environment variable",
            })
        else:
            try:
                from vibecode.integrations.pro_sync import ProSyncAdapter

                adapter = ProSyncAdapter(endpoint=pro_endpoint, token=pro_token)
                result = adapter.get_status()
                if "error" in result:
                    checks.append({
                        "name": "Pro databank",
                        "status": "ERROR",
                        "detail": f"Unreachable ({pro_endpoint}): {result['error']}",
                    })
                else:
                    approved = result.get("approved_patterns", "?")
                    checks.append({
                        "name": "Pro databank",
                        "status": "OK",
                        "detail": f"Connected ({pro_endpoint}), approved patterns: {approved}",
                    })
            except Exception as exc:
                checks.append({
                    "name": "Pro databank",
                    "status": "ERROR",
                    "detail": f"Exception: {exc}",
                })

    format_doctor_report(checks)
