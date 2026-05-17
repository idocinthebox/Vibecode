from __future__ import annotations

from pathlib import Path

from vibecode.db.sqlite_connection import get_connection
from vibecode.db.sqlite_schema import create_schema
from vibecode.models import FailurePattern
from vibecode.repositories.failure_repository import FailureRepository


def test_create_failure_pattern(temp_base: Path) -> None:
    conn = get_connection(temp_base)
    create_schema(conn)
    repo = FailureRepository(conn)
    pattern = FailurePattern(
        failure_id="f1",
        task_intent="Fix audio",
        bad_suggestion="Use external player",
        failure_reason="User wanted embedded",
        prevention_rule="Do not use external player",
        severity="high",
    )
    repo.create(pattern)
    fetched = repo.get_by_id("f1")
    assert fetched is not None
    assert fetched.severity == "high"
    conn.close()


def test_soft_delete_hides_memory_from_search(temp_base: Path) -> None:
    conn = get_connection(temp_base)
    create_schema(conn)
    repo = FailureRepository(conn)
    repo.create(
        FailurePattern(
            failure_id="f1",
            task_intent="Fix audio",
            bad_suggestion="Bad",
            failure_reason="Broke",
            prevention_rule="No",
            severity="medium",
        )
    )
    assert len(repo.search("audio")) == 1
    repo.soft_delete("f1")
    assert len(repo.search("audio")) == 0
    conn.close()
