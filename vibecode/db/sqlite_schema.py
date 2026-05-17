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
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

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


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()
