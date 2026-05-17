from __future__ import annotations

from pathlib import Path

import typer

from vibecode.cli.console import get_console, print_info, print_success
from vibecode.cli.formatters import format_report
from vibecode.cli.config_manager import ConfigManager
from vibecode.config.paths import get_vibecode_dir
from vibecode.db.sqlite_connection import get_connection, get_db_path
from vibecode.storage.json_store import JsonStore


def cmd_report(
    days: int = 30,
    project: str | None = None,
    fmt: str = "table",
    output: str | None = None,
) -> None:
    base = get_vibecode_dir()
    conn = get_connection(base) if get_db_path(base).exists() else None

    if conn:
        cursor = conn.execute("SELECT COUNT(*) AS c FROM success_patterns WHERE is_active = 1")
        success_count = cursor.fetchone()["c"]
        cursor = conn.execute("SELECT COUNT(*) AS c FROM failure_patterns WHERE is_active = 1")
        failure_count = cursor.fetchone()["c"]
        cursor = conn.execute("SELECT COUNT(*) AS c FROM project_rules WHERE is_active = 1")
        rule_count = cursor.fetchone()["c"]
        cursor = conn.execute(
            "SELECT COALESCE(SUM(estimated_tokens_saved), 0) AS total FROM success_patterns WHERE is_active = 1"
        )
        total_saved = cursor.fetchone()["total"]
        cursor = conn.execute(
            "SELECT name, usage_count FROM success_patterns WHERE is_active = 1 AND usage_count > 0 ORDER BY usage_count DESC LIMIT 5"
        )
        most_used = [(r["name"], r["usage_count"]) for r in cursor.fetchall()]
        cursor = conn.execute(
            "SELECT severity, task_intent FROM failure_patterns WHERE severity IN ('critical', 'high') LIMIT 5"
        )
        highest_severity = [(r["severity"], r["task_intent"]) for r in cursor.fetchall()]
        conn.close()
    else:
        success_store = JsonStore(base / "success_patterns")
        failure_store = JsonStore(base / "failure_patterns")
        rule_store = JsonStore(base / "project_rules")
        success_count = success_store.count()
        failure_count = failure_store.count()
        rule_count = rule_store.count()
        total_saved = 0
        most_used = []
        for data in success_store.load_all():
            total_saved += data.get("estimated_tokens_saved", 0)
            usage = data.get("usage_count", 0)
            if usage > 0:
                most_used.append((data.get("name", "Unknown"), usage))
        highest_severity = []
        for data in failure_store.load_all():
            if data.get("severity") in ("critical", "high"):
                highest_severity.append((data.get("severity", ""), data.get("task_intent", "Unknown")))

    data = {
        "success_patterns": success_count,
        "failure_patterns": failure_count,
        "project_rules": rule_count,
        "estimated_tokens_saved": total_saved,
        "days": days,
        "most_used": most_used[:5],
        "highest_severity": highest_severity[:5],
    }

    if fmt == "json":
        import json
        text = json.dumps(data, indent=2)
        if output:
            Path(output).write_text(text, encoding="utf-8")
            print_success(f"Report written to {output}")
        else:
            typer.echo(text)
    elif fmt == "markdown":
        text = format_report(data, fmt="markdown")
        if output:
            Path(output).write_text(text, encoding="utf-8")
            print_success(f"Report written to {output}")
        else:
            typer.echo(text)
    else:
        format_report(data, fmt="table")
        if output:
            text = format_report(data, fmt="markdown")
            Path(output).write_text(text, encoding="utf-8")
            print_success(f"Report written to {output}")
