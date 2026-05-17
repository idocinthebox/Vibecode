from __future__ import annotations

from pathlib import Path

from vibecode.db.sqlite_connection import get_connection
from vibecode.db.sqlite_schema import create_schema
from vibecode.models import SuccessPattern
from vibecode.repositories.pattern_repository import PatternRepository


def test_create_success_pattern(temp_base: Path) -> None:
    conn = get_connection(temp_base)
    create_schema(conn)
    repo = PatternRepository(conn)
    pattern = SuccessPattern(
        pattern_id="p1",
        name="Test",
        intent_description="Intent",
        reasoning_summary="Summary",
    )
    repo.create(pattern)
    fetched = repo.get_by_id("p1")
    assert fetched is not None
    assert fetched.name == "Test"
    conn.close()


def test_list_active_and_soft_delete(temp_base: Path) -> None:
    conn = get_connection(temp_base)
    create_schema(conn)
    repo = PatternRepository(conn)
    repo.create(
        SuccessPattern(
            pattern_id="p1", name="A", intent_description="I", reasoning_summary="S"
        )
    )
    repo.create(
        SuccessPattern(
            pattern_id="p2", name="B", intent_description="I", reasoning_summary="S"
        )
    )
    assert len(repo.list_active()) == 2
    repo.soft_delete("p1")
    assert len(repo.list_active()) == 1
    assert repo.get_by_id("p1").is_active is False
    conn.close()


def test_search_returns_matches(temp_base: Path) -> None:
    conn = get_connection(temp_base)
    create_schema(conn)
    repo = PatternRepository(conn)
    repo.create(
        SuccessPattern(
            pattern_id="p1",
            name="PyInstaller fix",
            intent_description="Fix Qt conflict",
            reasoning_summary="Exclude PyQt5",
            tags=["build", "qt"],
        )
    )
    results = repo.search("Qt")
    assert len(results) == 1
    assert results[0].name == "PyInstaller fix"
    conn.close()


def test_duplicate_content_hash_is_detected(temp_base: Path) -> None:
    conn = get_connection(temp_base)
    create_schema(conn)
    repo = PatternRepository(conn)
    pattern = SuccessPattern(
        pattern_id="p1", name="Dup", intent_description="I", reasoning_summary="S", content_hash="abc123"
    )
    repo.create(pattern)
    fetched = repo.get_by_content_hash("abc123")
    assert fetched is not None
    assert fetched.pattern_id == "p1"
    conn.close()
