from __future__ import annotations

import pytest

from tests.postgres.conftest import PG_AVAILABLE
from vibecode.db.models import ProjectRule
from vibecode.db.repositories import PostgresProjectRuleRepository

pytestmark = pytest.mark.skipif(not PG_AVAILABLE, reason="PostgreSQL not available")


def test_create_project_rule(pg_session) -> None:
    repo = PostgresProjectRuleRepository(pg_session)
    rule = ProjectRule(
        rule_text="Use PySide6 only",
        rule_type="dependency",
        severity="critical",
    )
    created = repo.create(rule)
    assert created.id is not None
    assert created.rule_id is not None
