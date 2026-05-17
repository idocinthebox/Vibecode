from __future__ import annotations

import pytest

from tests.postgres.conftest import PG_AVAILABLE
from vibecode.db.models import FailurePattern, ProjectRule, SuccessPattern
from vibecode.db.repositories import (
    PostgresFailureRepository,
    PostgresPatternRepository,
    PostgresProjectRuleRepository,
    PostgresSearchRepository,
)

pytestmark = pytest.mark.skipif(not PG_AVAILABLE, reason="PostgreSQL not available")


def test_full_text_search_success_patterns(pg_session) -> None:
    repo = PostgresPatternRepository(pg_session)
    search_repo = PostgresSearchRepository(pg_session)
    repo.create(
        SuccessPattern(
            name="PyInstaller fix",
            intent_description="Fix Qt conflict",
            reasoning_summary="Exclude PyQt5",
            tags=["build", "qt"],
        )
    )
    results = search_repo.full_text_search_success("Qt conflict")
    assert len(results) >= 1


def test_full_text_search_failure_patterns(pg_session) -> None:
    repo = PostgresFailureRepository(pg_session)
    search_repo = PostgresSearchRepository(pg_session)
    repo.create(
        FailurePattern(
            task_intent="Fix Qt conflict",
            bad_suggestion="Mix Qt bindings",
            failure_reason="Causes packaging conflicts",
            prevention_rule="Do not mix Qt bindings",
            severity="high",
            tags=["qt"],
        )
    )
    results = search_repo.full_text_search_failure("Qt conflict")
    assert len(results) >= 1


def test_tag_filter_search(pg_session) -> None:
    repo = PostgresPatternRepository(pg_session)
    repo.create(
        SuccessPattern(
            name="Tag test",
            intent_description="I",
            reasoning_summary="S",
            tags=["python", "qt"],
        )
    )
    results = repo.search("python")
    assert len(results) == 1
