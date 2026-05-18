from __future__ import annotations

import sqlite3
from pathlib import Path

from vibecode.db.sqlite_connection import get_connection
from vibecode.db.sqlite_schema import create_schema

# A "v0.2-like" old schema: has the columns referenced by pre-Phase-0 indexes
# (language, content_hash, last_used, confidence, last_seen_at, severity,
# review_state) but lacks the Phase 0 additions: harvest_meta,
# shared_publication_id on all three tables, and source_type/source_ref on
# project_rules.
_OLD_SCHEMA_SQL = """
CREATE TABLE success_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id TEXT NOT NULL UNIQUE,
    project_id TEXT,
    name TEXT NOT NULL,
    intent_description TEXT NOT NULL,
    language TEXT,
    framework TEXT,
    confidence REAL NOT NULL DEFAULT 1.0,
    last_seen_at TEXT,
    content_hash TEXT,
    last_used TEXT,
    review_state TEXT NOT NULL DEFAULT 'confirmed',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE failure_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    failure_id TEXT NOT NULL UNIQUE,
    project_id TEXT,
    task_intent TEXT NOT NULL,
    bad_suggestion TEXT NOT NULL,
    failure_reason TEXT NOT NULL,
    prevention_rule TEXT NOT NULL,
    language TEXT,
    severity TEXT NOT NULL DEFAULT 'medium',
    confidence REAL NOT NULL DEFAULT 1.0,
    last_seen_at TEXT,
    content_hash TEXT,
    review_state TEXT NOT NULL DEFAULT 'confirmed',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE project_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id TEXT NOT NULL UNIQUE,
    project_id TEXT,
    rule_text TEXT NOT NULL,
    rule_type TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'medium',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}


def test_create_schema_backfills_phase0_columns_on_existing_db(temp_base: Path) -> None:
    # Simulate an existing pre-Phase-0 database.
    conn = get_connection(temp_base)
    conn.executescript(_OLD_SCHEMA_SQL)
    conn.execute(
        "INSERT INTO success_patterns (pattern_id, name, intent_description, created_at, updated_at) "
        "VALUES ('sp-old', 'old', 'old', '2026-01-01T00:00:00', '2026-01-01T00:00:00')"
    )
    conn.execute(
        "INSERT INTO failure_patterns (failure_id, task_intent, bad_suggestion, failure_reason, "
        "prevention_rule, created_at, updated_at) "
        "VALUES ('fp-old', 'i', 'b', 'r', 'p', '2026-01-01T00:00:00', '2026-01-01T00:00:00')"
    )
    conn.execute(
        "INSERT INTO project_rules (rule_id, rule_text, rule_type, created_at, updated_at) "
        "VALUES ('pr-old', 'rule', 'dependency', '2026-01-01T00:00:00', '2026-01-01T00:00:00')"
    )
    conn.commit()

    # Run schema migration.
    create_schema(conn)

    # New Phase 0 columns must be present on each table.
    sp_cols = _columns(conn, "success_patterns")
    fp_cols = _columns(conn, "failure_patterns")
    pr_cols = _columns(conn, "project_rules")

    assert {"harvest_meta", "shared_publication_id"} <= sp_cols
    assert {"harvest_meta", "shared_publication_id"} <= fp_cols
    assert {"source_type", "source_ref", "harvest_meta", "review_state", "shared_publication_id"} <= pr_cols

    # New tables must be created.
    table_names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "audit_log" in table_names
    assert "shared_publications" in table_names

    # Existing rows must be backfilled with defaults instead of NULL.
    sp_row = conn.execute(
        "SELECT harvest_meta, shared_publication_id FROM success_patterns WHERE pattern_id='sp-old'"
    ).fetchone()
    assert sp_row["harvest_meta"] == "{}"
    assert sp_row["shared_publication_id"] is None

    pr_row = conn.execute(
        "SELECT source_type, review_state, harvest_meta FROM project_rules WHERE rule_id='pr-old'"
    ).fetchone()
    assert pr_row["source_type"] == "manual"
    assert pr_row["review_state"] == "confirmed"
    assert pr_row["harvest_meta"] == "{}"

    conn.close()
