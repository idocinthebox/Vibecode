from __future__ import annotations

import json
from pathlib import Path

import typer

from vibecode.cli.console import print_error, print_info, print_success
from vibecode.config.paths import get_vibecode_dir
from vibecode.core.security import redact_secrets
from vibecode.db.sqlite_connection import get_connection, get_db_path
from vibecode.services.export_service import ExportService
from vibecode.storage.json_store import JsonStore


def cmd_export(
    fmt: str = "markdown",
    output: str | None = None,
) -> None:
    base = get_vibecode_dir()
    conn = get_connection(base) if get_db_path(base).exists() else None
    service = ExportService(base, conn)
    paths = service.export_all()
    if conn:
        conn.close()
    for p in paths:
        print_success(f"Exported: {p}")

    if fmt == "json":
        _export_json(base, output)
    elif output:
        print_success(f"Export written to {output}")


def _export_json(base: Path, output: str | None = None) -> None:
    data = {
        "version": "1.0",
        "success_patterns": [],
        "failure_patterns": [],
        "project_rules": [],
    }
    conn = get_connection(base) if get_db_path(base).exists() else None
    if conn:
        cursor = conn.execute("SELECT * FROM success_patterns WHERE is_active = 1")
        for row in cursor.fetchall():
            data["success_patterns"].append(dict(row))
        cursor = conn.execute("SELECT * FROM failure_patterns WHERE is_active = 1")
        for row in cursor.fetchall():
            data["failure_patterns"].append(dict(row))
        cursor = conn.execute("SELECT * FROM project_rules WHERE is_active = 1")
        for row in cursor.fetchall():
            data["project_rules"].append(dict(row))
        conn.close()
    else:
        for label, store in [
            ("success_patterns", JsonStore(base / "success_patterns")),
            ("failure_patterns", JsonStore(base / "failure_patterns")),
            ("project_rules", JsonStore(base / "project_rules")),
        ]:
            data[label] = store.load_all()

    text = json.dumps(data, indent=2)
    if output:
        Path(output).write_text(text, encoding="utf-8")
        print_success(f"JSON export written to {output}")
    else:
        typer.echo(text)


def cmd_import_file(
    path: str,
    skip_duplicates: bool = True,
) -> None:
    base = get_vibecode_dir()
    filepath = Path(path)
    if not filepath.exists():
        print_error(f"File not found: {path}")
        raise typer.Exit(1)

    raw = filepath.read_text(encoding="utf-8")
    data = json.loads(raw)

    if not isinstance(data, dict) or "version" not in data:
        print_error("Invalid import file: missing version field.")
        raise typer.Exit(1)

    conn = get_connection(base) if get_db_path(base).exists() else None
    from vibecode.services.capture_service import CaptureService

    capture = CaptureService(base, conn)
    counts = {"success": 0, "failure": 0, "rules": 0, "skipped": 0}

    for item in data.get("success_patterns", []):
        item = {k: redact_secrets(v) if isinstance(v, str) else v for k, v in item.items()}
        _, created = capture.capture_success(item)
        if created:
            counts["success"] += 1
        else:
            counts["skipped"] += 1

    for item in data.get("failure_patterns", []):
        item = {k: redact_secrets(v) if isinstance(v, str) else v for k, v in item.items()}
        _, created = capture.capture_failure(item)
        if created:
            counts["failure"] += 1
        else:
            counts["skipped"] += 1

    for item in data.get("project_rules", []):
        item = {k: redact_secrets(v) if isinstance(v, str) else v for k, v in item.items()}
        capture.add_rule(item)
        counts["rules"] += 1

    if conn:
        conn.close()

    print_success(f"Import complete:")
    print_info(f"  Success patterns: {counts['success']}")
    print_info(f"  Failure patterns: {counts['failure']}")
    print_info(f"  Project rules: {counts['rules']}")
    print_info(f"  Skipped (duplicates): {counts['skipped']}")
