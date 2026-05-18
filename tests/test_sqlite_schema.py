from __future__ import annotations

from pathlib import Path

from vibecode.db.sqlite_connection import get_connection
from vibecode.db.sqlite_schema import create_schema


def test_schema_contains_required_tables(temp_base: Path) -> None:
    conn = get_connection(temp_base)
    create_schema(conn)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = {row["name"] for row in cursor.fetchall()}
    required = {
        "success_patterns",
        "failure_patterns",
        "project_rules",
        "shared_publications",
        "audit_log",
        "agent_profiles",
        "usage_events",
        "projects",
    }
    assert required.issubset(tables)

    cursor = conn.execute("PRAGMA table_info(project_rules)")
    rule_columns = {row["name"] for row in cursor.fetchall()}
    assert {"source_type", "source_ref", "harvest_meta", "review_state", "shared_publication_id"}.issubset(rule_columns)
    conn.close()
