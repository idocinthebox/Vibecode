from __future__ import annotations

import sqlite3

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    root_path TEXT,
    description TEXT,
    project_hash TEXT,
    settings_json TEXT NOT NULL DEFAULT '{}',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS success_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id TEXT NOT NULL UNIQUE,
    project_id TEXT,
    name TEXT NOT NULL,
    intent_description TEXT NOT NULL,
    language TEXT,
    framework TEXT,
    file_type TEXT,
    tags_json TEXT NOT NULL DEFAULT '[]',
    affected_files_json TEXT NOT NULL DEFAULT '[]',
    original_prompt TEXT,
    reasoning_summary TEXT,
    reasoning_steps_json TEXT NOT NULL DEFAULT '[]',
    code_before TEXT,
    code_after TEXT,
    diff TEXT,
    explanation TEXT,
    token_cost_original INTEGER NOT NULL DEFAULT 0,
    token_cost_retrieval INTEGER NOT NULL DEFAULT 0,
    estimated_tokens_saved INTEGER NOT NULL DEFAULT 0,
    confidence_score REAL NOT NULL DEFAULT 1.0,
    usage_count INTEGER NOT NULL DEFAULT 0,
    success_rate REAL NOT NULL DEFAULT 1.0,
    confidence REAL NOT NULL DEFAULT 1.0,
    occurrence_count INTEGER NOT NULL DEFAULT 1,
    last_seen_at TEXT,
    agent_source TEXT,
    review_state TEXT NOT NULL DEFAULT 'confirmed',
    source_type TEXT,
    source_ref TEXT,
    source_commit TEXT,
    source_file_path TEXT,
    content_hash TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_used TEXT
);

CREATE INDEX IF NOT EXISTS idx_success_patterns_project
ON success_patterns(project_id);

CREATE INDEX IF NOT EXISTS idx_success_patterns_language
ON success_patterns(language);

CREATE INDEX IF NOT EXISTS idx_success_patterns_content_hash
ON success_patterns(content_hash);

CREATE INDEX IF NOT EXISTS idx_success_patterns_last_used
ON success_patterns(last_used);

CREATE INDEX IF NOT EXISTS idx_success_patterns_review_state
ON success_patterns(review_state);

CREATE INDEX IF NOT EXISTS idx_success_patterns_confidence
ON success_patterns(confidence DESC, last_seen_at DESC);

CREATE TABLE IF NOT EXISTS failure_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    failure_id TEXT NOT NULL UNIQUE,
    project_id TEXT,
    task_intent TEXT NOT NULL,
    bad_suggestion TEXT NOT NULL,
    failure_reason TEXT NOT NULL,
    corrected_approach TEXT,
    prevention_rule TEXT NOT NULL,
    language TEXT,
    framework TEXT,
    affected_files_json TEXT NOT NULL DEFAULT '[]',
    tags_json TEXT NOT NULL DEFAULT '[]',
    severity TEXT NOT NULL DEFAULT 'medium',
    confidence_score REAL NOT NULL DEFAULT 1.0,
    usage_count INTEGER NOT NULL DEFAULT 0,
    confidence REAL NOT NULL DEFAULT 1.0,
    occurrence_count INTEGER NOT NULL DEFAULT 1,
    last_seen_at TEXT,
    agent_source TEXT,
    review_state TEXT NOT NULL DEFAULT 'confirmed',
    source_type TEXT,
    source_ref TEXT,
    source_commit TEXT,
    source_file_path TEXT,
    content_hash TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_used TEXT
);

CREATE INDEX IF NOT EXISTS idx_failure_patterns_project
ON failure_patterns(project_id);

CREATE INDEX IF NOT EXISTS idx_failure_patterns_language
ON failure_patterns(language);

CREATE INDEX IF NOT EXISTS idx_failure_patterns_severity
ON failure_patterns(severity);

CREATE INDEX IF NOT EXISTS idx_failure_patterns_content_hash
ON failure_patterns(content_hash);

CREATE INDEX IF NOT EXISTS idx_failure_patterns_review_state
ON failure_patterns(review_state);

CREATE INDEX IF NOT EXISTS idx_failure_patterns_confidence
ON failure_patterns(confidence DESC, last_seen_at DESC);

CREATE TABLE IF NOT EXISTS project_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id TEXT NOT NULL UNIQUE,
    project_id TEXT,
    rule_text TEXT NOT NULL,
    rule_type TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'medium',
    source_success_pattern_id TEXT,
    source_failure_id TEXT,
    tags_json TEXT NOT NULL DEFAULT '[]',
    source_type TEXT NOT NULL DEFAULT 'manual',
    source_ref TEXT,
    harvest_meta TEXT NOT NULL DEFAULT '{}',
    review_state TEXT NOT NULL DEFAULT 'confirmed',
    shared_publication_id TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_project_rules_review_state
ON project_rules(review_state);

CREATE TABLE IF NOT EXISTS shared_publications (
    id TEXT PRIMARY KEY,
    local_pattern_id TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    scope TEXT NOT NULL,
    submission_id TEXT NOT NULL,
    moderation_state TEXT NOT NULL,
    published_at TEXT,
    retracted_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_shared_publications_local_pattern
ON shared_publications(local_pattern_id);

CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    ts TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    project_path TEXT,
    meta TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_audit_log_actor_action
ON audit_log(actor, action, ts DESC);

CREATE INDEX IF NOT EXISTS idx_audit_log_target
ON audit_log(target_type, target_id, ts DESC);

CREATE TABLE IF NOT EXISTS agent_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    target_agent TEXT NOT NULL,
    max_context_tokens INTEGER NOT NULL DEFAULT 1500,
    include_success_patterns INTEGER NOT NULL DEFAULT 1,
    include_failure_patterns INTEGER NOT NULL DEFAULT 1,
    include_project_rules INTEGER NOT NULL DEFAULT 1,
    include_recent_usage INTEGER NOT NULL DEFAULT 0,
    output_format TEXT NOT NULL DEFAULT 'markdown',
    template_path TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS usage_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    project_id TEXT,
    memory_type TEXT NOT NULL,
    memory_id TEXT NOT NULL,
    query_text TEXT,
    agent_profile TEXT,
    tokens_saved INTEGER NOT NULL DEFAULT 0,
    retrieval_time_ms INTEGER,
    was_useful INTEGER,
    was_modified INTEGER,
    created_at TEXT NOT NULL
);
"""


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def _add_column_if_missing(
    conn: sqlite3.Connection,
    table_name: str,
    column_name: str,
    ddl: str,
) -> None:
    # Safe to call before the table exists: silently skip in that case so
    # this helper can run BEFORE executescript on a pre-existing DB.
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    if not exists:
        return
    columns = _table_columns(conn, table_name)
    if column_name not in columns:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")


def _ensure_phase0_columns(conn: sqlite3.Connection) -> None:
    # success_patterns/failure_patterns already include some Phase 0 columns in
    # fresh schema; this keeps older databases forward-compatible.
    _add_column_if_missing(conn, "success_patterns", "source_type", "source_type TEXT")
    _add_column_if_missing(conn, "success_patterns", "source_ref", "source_ref TEXT")
    _add_column_if_missing(
        conn,
        "success_patterns",
        "harvest_meta",
        "harvest_meta TEXT NOT NULL DEFAULT '{}'",
    )
    _add_column_if_missing(
        conn,
        "success_patterns",
        "shared_publication_id",
        "shared_publication_id TEXT",
    )

    _add_column_if_missing(conn, "failure_patterns", "source_type", "source_type TEXT")
    _add_column_if_missing(conn, "failure_patterns", "source_ref", "source_ref TEXT")
    _add_column_if_missing(
        conn,
        "failure_patterns",
        "harvest_meta",
        "harvest_meta TEXT NOT NULL DEFAULT '{}'",
    )
    _add_column_if_missing(
        conn,
        "failure_patterns",
        "shared_publication_id",
        "shared_publication_id TEXT",
    )

    _add_column_if_missing(
        conn,
        "project_rules",
        "source_type",
        "source_type TEXT NOT NULL DEFAULT 'manual'",
    )
    _add_column_if_missing(conn, "project_rules", "source_ref", "source_ref TEXT")
    _add_column_if_missing(
        conn,
        "project_rules",
        "harvest_meta",
        "harvest_meta TEXT NOT NULL DEFAULT '{}'",
    )
    _add_column_if_missing(
        conn,
        "project_rules",
        "review_state",
        "review_state TEXT NOT NULL DEFAULT 'confirmed'",
    )
    _add_column_if_missing(
        conn,
        "project_rules",
        "shared_publication_id",
        "shared_publication_id TEXT",
    )


def _backfill_phase0_defaults(conn: sqlite3.Connection) -> None:
    conn.execute("UPDATE success_patterns SET source_type = 'manual' WHERE source_type IS NULL OR source_type = ''")
    conn.execute("UPDATE failure_patterns SET source_type = 'manual' WHERE source_type IS NULL OR source_type = ''")
    conn.execute("UPDATE project_rules SET source_type = 'manual' WHERE source_type IS NULL OR source_type = ''")

    conn.execute(
        "UPDATE success_patterns SET review_state = 'confirmed' WHERE review_state IS NULL OR review_state = ''"
    )
    conn.execute(
        "UPDATE failure_patterns SET review_state = 'confirmed' WHERE review_state IS NULL OR review_state = ''"
    )
    conn.execute("UPDATE project_rules SET review_state = 'confirmed' WHERE review_state IS NULL OR review_state = ''")

    conn.execute("UPDATE success_patterns SET harvest_meta = '{}' WHERE harvest_meta IS NULL OR harvest_meta = ''")
    conn.execute("UPDATE failure_patterns SET harvest_meta = '{}' WHERE harvest_meta IS NULL OR harvest_meta = ''")
    conn.execute("UPDATE project_rules SET harvest_meta = '{}' WHERE harvest_meta IS NULL OR harvest_meta = ''")


def create_schema(conn: sqlite3.Connection) -> None:
    # Ensure Phase 0 columns exist on any pre-existing tables BEFORE running
    # the schema script, because SCHEMA_SQL contains CREATE INDEX statements
    # that reference those columns (e.g. review_state). Without this, a DB
    # created by an earlier VibeCode version raises
    # `sqlite3.OperationalError: no such column: review_state`.
    _ensure_phase0_columns(conn)
    conn.executescript(SCHEMA_SQL)
    _ensure_phase0_columns(conn)
    _backfill_phase0_defaults(conn)
    conn.commit()
