"""SQLite schema for the Pro Databank server.

Provides DDL and helpers for the shared pattern databank.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

PRO_SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS databank_patterns (
    id            TEXT PRIMARY KEY,
    memory_type   TEXT NOT NULL CHECK(memory_type IN ('success_pattern','failure_pattern','project_rule')),
    title         TEXT NOT NULL,
    summary       TEXT NOT NULL,
    body_json     TEXT NOT NULL DEFAULT '{}',
    language      TEXT NOT NULL DEFAULT '',
    framework     TEXT NOT NULL DEFAULT '',
    tags          TEXT NOT NULL DEFAULT '[]',
    submitted_by  TEXT NOT NULL DEFAULT 'anonymous',
    review_state  TEXT NOT NULL DEFAULT 'pending' CHECK(review_state IN ('pending','approved','rejected')),
    usefulness    REAL NOT NULL DEFAULT 0.0,
    feedback_count INTEGER NOT NULL DEFAULT 0,
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS databank_feedback (
    id              TEXT PRIMARY KEY,
    pattern_id      TEXT NOT NULL REFERENCES databank_patterns(id),
    was_useful      INTEGER NOT NULL,
    submitted_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS moderation_log (
    id              TEXT PRIMARY KEY,
    pattern_id      TEXT NOT NULL REFERENCES databank_patterns(id),
    action          TEXT NOT NULL CHECK(action IN ('approve','reject','escalate')),
    moderator       TEXT NOT NULL DEFAULT 'system',
    reason          TEXT NOT NULL DEFAULT '',
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE INDEX IF NOT EXISTS idx_patterns_memory_type ON databank_patterns(memory_type, review_state, is_active);
CREATE INDEX IF NOT EXISTS idx_patterns_language ON databank_patterns(language);
CREATE INDEX IF NOT EXISTS idx_feedback_pattern ON databank_feedback(pattern_id);
"""


def get_pro_db_path(data_dir: Path) -> Path:
    return data_dir / "pro_databank.db"


def get_pro_connection(data_dir: Path) -> sqlite3.Connection:
    db_path = get_pro_db_path(data_dir)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(PRO_SCHEMA_SQL)
    conn.commit()
    return conn
