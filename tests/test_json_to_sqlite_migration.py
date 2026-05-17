from __future__ import annotations

import json
from pathlib import Path

from vibecode.db.sqlite_connection import get_connection
from vibecode.db.sqlite_schema import create_schema
from vibecode.repositories.agent_profile_repository import AgentProfileRepository
from vibecode.repositories.failure_repository import FailureRepository
from vibecode.repositories.pattern_repository import PatternRepository
from vibecode.repositories.rule_repository import RuleRepository
from vibecode.services.migration_service import MigrationService


def test_json_to_sqlite_migration_preserves_ids(temp_base: Path) -> None:
    # Seed JSON files
    success = {
        "pattern_id": "sp-abc",
        "name": "JSON Success",
        "intent_description": "Intent",
        "reasoning_summary": "Summary",
        "content_hash": "hash123",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00+00:00",
        "updated_at": "2024-01-01T00:00:00+00:00",
    }
    failure = {
        "failure_id": "fp-def",
        "task_intent": "Fix thing",
        "bad_suggestion": "Bad",
        "failure_reason": "Broke",
        "prevention_rule": "No",
        "severity": "high",
        "content_hash": "hash456",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00+00:00",
        "updated_at": "2024-01-01T00:00:00+00:00",
    }
    rule = {
        "rule_id": "pr-ghi",
        "rule_text": "Rule text",
        "rule_type": "dependency",
        "severity": "medium",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00+00:00",
        "updated_at": "2024-01-01T00:00:00+00:00",
    }
    profile = {
        "profile_id": "ap-jkl",
        "name": "test-profile",
        "target_agent": "Test",
        "max_context_tokens": 1000,
        "created_at": "2024-01-01T00:00:00+00:00",
        "updated_at": "2024-01-01T00:00:00+00:00",
    }

    (temp_base / "success_patterns").mkdir(parents=True, exist_ok=True)
    (temp_base / "failure_patterns").mkdir(parents=True, exist_ok=True)
    (temp_base / "project_rules").mkdir(parents=True, exist_ok=True)
    (temp_base / "agent_profiles").mkdir(parents=True, exist_ok=True)

    (temp_base / "success_patterns" / "sp-abc.json").write_text(
        json.dumps(success), encoding="utf-8"
    )
    (temp_base / "failure_patterns" / "fp-def.json").write_text(
        json.dumps(failure), encoding="utf-8"
    )
    (temp_base / "project_rules" / "pr-ghi.json").write_text(
        json.dumps(rule), encoding="utf-8"
    )
    (temp_base / "agent_profiles" / "ap-jkl.json").write_text(
        json.dumps(profile), encoding="utf-8"
    )

    conn = get_connection(temp_base)
    create_schema(conn)

    service = MigrationService(temp_base, conn)
    counts = service.migrate()

    assert counts["success_patterns"] == 1
    assert counts["failure_patterns"] == 1
    assert counts["project_rules"] == 1
    assert counts["agent_profiles"] == 1
    assert counts["duplicates_skipped"] == 0

    pattern_repo = PatternRepository(conn)
    failure_repo = FailureRepository(conn)
    rule_repo = RuleRepository(conn)
    profile_repo = AgentProfileRepository(conn)

    assert pattern_repo.get_by_id("sp-abc") is not None
    assert failure_repo.get_by_id("fp-def") is not None
    assert rule_repo.get_by_id("pr-ghi") is not None
    assert profile_repo.get_by_id("ap-jkl") is not None
    conn.close()


def test_duplicate_content_hash_is_skipped(temp_base: Path) -> None:
    success = {
        "pattern_id": "sp-abc",
        "name": "JSON Success",
        "intent_description": "Intent",
        "reasoning_summary": "Summary",
        "content_hash": "samehash",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00+00:00",
        "updated_at": "2024-01-01T00:00:00+00:00",
    }
    (temp_base / "success_patterns").mkdir(parents=True, exist_ok=True)
    (temp_base / "success_patterns" / "sp-abc.json").write_text(
        json.dumps(success), encoding="utf-8"
    )
    (temp_base / "success_patterns" / "sp-abc2.json").write_text(
        json.dumps({**success, "pattern_id": "sp-abc2"}), encoding="utf-8"
    )

    conn = get_connection(temp_base)
    create_schema(conn)

    service = MigrationService(temp_base, conn)
    counts = service.migrate()

    assert counts["success_patterns"] == 1
    assert counts["duplicates_skipped"] == 1
    conn.close()
