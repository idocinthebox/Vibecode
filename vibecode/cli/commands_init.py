from __future__ import annotations

from pathlib import Path

import typer

from vibecode.cli.console import print_info, print_success, print_warning
from vibecode.cli.errors import StorageNotInitializedError
from vibecode.config.paths import get_vibecode_dir
from vibecode.db.sqlite_connection import get_connection, get_db_path
from vibecode.db.sqlite_schema import create_schema
from vibecode.services.capture_service import CaptureService
from vibecode.services.migration_service import MigrationService
from vibecode.storage.json_store import JsonStore


def _get_base_dir() -> Path:
    return get_vibecode_dir()


def _get_conn(base_dir: Path | None = None):
    db_path = get_db_path(base_dir)
    if db_path.exists():
        return get_connection(base_dir)
    return None


def cmd_init() -> None:
    base = _get_base_dir()
    dirs = [
        base / "success_patterns",
        base / "failure_patterns",
        base / "project_rules",
        base / "agent_profiles",
        base / "token_reports",
        base / "exports",
    ]
    created_any = False
    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            print_success(f"Created: {d}")
            created_any = True
        else:
            print_info(f"Exists:  {d}")

    config_path = base / "config.json"
    if not config_path.exists():
        config_path.write_text('{"version": "0.1.0"}', encoding="utf-8")
        print_success(f"Created: {config_path}")
        created_any = True
    else:
        print_info(f"Exists:  {config_path}")

    capture = CaptureService(base)
    capture.seed_profiles()
    print_success("Seeded default agent profiles.")

    if created_any:
        print_success("VibeCode initialized.")
    else:
        print_warning("VibeCode already initialized.")


def cmd_init_db() -> None:
    base = _get_base_dir()
    conn = get_connection(base)
    create_schema(conn)
    conn.close()
    capture = CaptureService(base, get_connection(base))
    capture.seed_profiles()
    capture.conn.close()
    print_success(f"SQLite database initialized: {get_db_path(base)}")


def cmd_db_status() -> None:
    base = _get_base_dir()
    db_path = get_db_path(base)
    if not db_path.exists():
        print_warning("SQLite database not found. Run: vibecode init-db")
        raise typer.Exit(1)
    conn = get_connection(base)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row["name"] for row in cursor.fetchall()]
    conn.close()
    print_info(f"Database: {db_path}")
    for t in tables:
        print_info(f"  Table: {t}")


def cmd_migrate_json_to_sqlite() -> None:
    base = _get_base_dir()
    if not base.exists():
        raise StorageNotInitializedError()
    db_path = get_db_path(base)
    if not db_path.exists():
        raise StorageNotInitializedError()

    service = MigrationService(base)
    counts = service.migrate()
    print_success("Migration complete:")
    print_info(f"  success patterns: {counts['success_patterns']}")
    print_info(f"  failure patterns: {counts['failure_patterns']}")
    print_info(f"  project rules: {counts['project_rules']}")
    print_info(f"  agent profiles: {counts['agent_profiles']}")
    print_info(f"  duplicates skipped: {counts['duplicates_skipped']}")
    print_info(f"  errors: {counts['errors']}")


def cmd_status() -> None:
    base = _get_base_dir()
    if not base.exists():
        raise StorageNotInitializedError()

    conn = _get_conn(base)
    if conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        for row in cursor.fetchall():
            print_info(f"Table: {row['name']}")
        conn.close()
    else:
        stores = {
            "Success patterns": JsonStore(base / "success_patterns"),
            "Failure patterns": JsonStore(base / "failure_patterns"),
            "Project rules": JsonStore(base / "project_rules"),
            "Agent profiles": JsonStore(base / "agent_profiles"),
        }
        for label, store in stores.items():
            print_info(f"{label}: {store.count()}")
