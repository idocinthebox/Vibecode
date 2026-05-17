from __future__ import annotations

import pytest

from tests.postgres.conftest import PG_AVAILABLE
from vibecode.db.models import FailurePattern
from vibecode.db.repositories import PostgresFailureRepository

pytestmark = pytest.mark.skipif(not PG_AVAILABLE, reason="PostgreSQL not available")


def test_create_failure_pattern(pg_session) -> None:
    repo = PostgresFailureRepository(pg_session)
    pattern = FailurePattern(
        task_intent="Fix audio",
        bad_suggestion="Use external player",
        failure_reason="User wanted embedded",
        prevention_rule="Do not use external player",
        severity="high",
    )
    created = repo.create(pattern)
    assert created.id is not None
    assert created.failure_id is not None
