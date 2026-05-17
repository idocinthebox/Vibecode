from __future__ import annotations

import pytest
from sqlalchemy import inspect

from tests.postgres.conftest import PG_AVAILABLE

pytestmark = pytest.mark.skipif(not PG_AVAILABLE, reason="PostgreSQL not available")


def test_postgres_container_starts(pg_engine) -> None:
    with pg_engine.connect() as conn:
        result = conn.execute("SELECT 1")
        assert result.scalar() == 1


def test_required_extensions_exist(pg_engine) -> None:
    with pg_engine.connect() as conn:
        for ext in ("pgcrypto", "pg_trgm", "vector"):
            result = conn.execute(
                f"SELECT 1 FROM pg_extension WHERE extname = '{ext}'"
            )
            assert result.scalar() == 1, f"Extension {ext} not installed"


def test_alembic_upgrade_head(pg_engine) -> None:
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    inspector = inspect(pg_engine)
    tables = inspector.get_table_names()
    assert "success_patterns" in tables
    assert "failure_patterns" in tables
    assert "project_rules" in tables
    assert "agent_profiles" in tables
    assert "usage_events" in tables


def test_alembic_downgrade_base(pg_engine) -> None:
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    command.downgrade(alembic_cfg, "base")

    inspector = inspect(pg_engine)
    tables = inspector.get_table_names()
    assert "success_patterns" not in tables
