from __future__ import annotations

from pathlib import Path

from vibecode.db.sqlite_connection import get_connection
from vibecode.db.sqlite_schema import create_schema
from vibecode.models import ProjectRule
from vibecode.repositories.rule_repository import RuleRepository


def test_create_project_rule(temp_base: Path) -> None:
    conn = get_connection(temp_base)
    create_schema(conn)
    repo = RuleRepository(conn)
    rule = ProjectRule(
        rule_id="r1",
        rule_text="Use PySide6 only",
        rule_type="dependency",
        severity="critical",
    )
    repo.create(rule)
    fetched = repo.get_by_id("r1")
    assert fetched is not None
    assert fetched.severity == "critical"
    conn.close()
