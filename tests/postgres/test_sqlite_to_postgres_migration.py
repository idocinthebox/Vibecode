from __future__ import annotations

import pytest

from tests.postgres.conftest import PG_AVAILABLE
from vibecode.db.models import (
    AgentProfile,
    FailurePattern,
    ProjectRule,
    SuccessPattern,
)
from vibecode.db.repositories import (
    PostgresAgentProfileRepository,
    PostgresFailureRepository,
    PostgresPatternRepository,
    PostgresProjectRuleRepository,
)

pytestmark = pytest.mark.skipif(not PG_AVAILABLE, reason="PostgreSQL not available")


def test_sqlite_to_postgres_migration_preserves_ids(pg_session, tmp_path) -> None:
    from vibecode.services.sqlite_to_postgres_migration_service import (
        SqliteToPostgresMigrationService,
    )

    # Create a minimal SQLite DB with one success pattern
    import sqlite3

    sqlite_path = tmp_path / "vibecode.db"
    conn = sqlite3.connect(str(sqlite_path))
    conn.executescript(
        """
        CREATE TABLE success_patterns (
            pattern_id TEXT PRIMARY KEY,
            name TEXT,
            intent_description TEXT,
            reasoning_summary TEXT,
            tags_json TEXT DEFAULT '[]',
            affected_files_json TEXT DEFAULT '[]',
            reasoning_steps_json TEXT DEFAULT '[]',
            language TEXT,
            framework TEXT,
            file_type TEXT,
            original_prompt TEXT,
            code_before TEXT,
            code_after TEXT,
            diff TEXT,
            explanation TEXT,
            token_cost_original INTEGER DEFAULT 0,
            token_cost_retrieval INTEGER DEFAULT 0,
            estimated_tokens_saved INTEGER DEFAULT 0,
            confidence_score REAL DEFAULT 1.0,
            usage_count INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 1.0,
            source_type TEXT,
            source_ref TEXT,
            source_commit TEXT,
            source_file_path TEXT,
            content_hash TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT,
            last_used TEXT
        );
        INSERT INTO success_patterns (pattern_id, name, intent_description, reasoning_summary, created_at, updated_at)
        VALUES ('sp-abc', 'Test', 'Intent', 'Summary', '2024-01-01T00:00:00+00:00', '2024-01-01T00:00:00+00:00');
        """
    )
    conn.commit()
    conn.close()

    service = SqliteToPostgresMigrationService(sqlite_path, pg_session)
    counts = service.migrate()

    assert counts["success_patterns"] == 1
    repo = PostgresPatternRepository(pg_session)
    fetched = repo.get_by_uuid("sp-abc")
    assert fetched is not None
    assert fetched.name == "Test"
