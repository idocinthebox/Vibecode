from __future__ import annotations

import pytest
from sqlalchemy import inspect

from tests.postgres.conftest import PG_AVAILABLE
from vibecode.db.models import SuccessPattern
from vibecode.db.repositories import PostgresPatternRepository

pytestmark = pytest.mark.skipif(not PG_AVAILABLE, reason="PostgreSQL not available")


def test_create_success_pattern(pg_session) -> None:
    repo = PostgresPatternRepository(pg_session)
    pattern = SuccessPattern(
        name="Test",
        intent_description="Intent",
        reasoning_summary="Summary",
    )
    created = repo.create(pattern)
    assert created.id is not None
    assert created.pattern_id is not None


def test_soft_delete_hides_records(pg_session) -> None:
    repo = PostgresPatternRepository(pg_session)
    pattern = SuccessPattern(
        name="Del",
        intent_description="I",
        reasoning_summary="S",
    )
    created = repo.create(pattern)
    repo.soft_delete(created.pattern_id)
    assert repo.get_by_uuid(created.pattern_id).is_active is False
    assert len(repo.list_active()) == 0


def test_content_hash_dedupe(pg_session) -> None:
    repo = PostgresPatternRepository(pg_session)
    p1 = SuccessPattern(
        name="Dup",
        intent_description="I",
        reasoning_summary="S",
        content_hash="samehash123",
    )
    repo.create(p1)
    p2 = repo.get_by_content_hash("samehash123")
    assert p2 is not None
    assert p2.name == "Dup"
