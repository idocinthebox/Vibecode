from __future__ import annotations

import pytest
from sqlalchemy import inspect

from tests.postgres.conftest import PG_AVAILABLE

pytestmark = pytest.mark.skipif(not PG_AVAILABLE, reason="PostgreSQL not available")


def test_alembic_smoke(pg_engine) -> None:
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    inspector = inspect(pg_engine)
    assert "success_patterns" in inspector.get_table_names()
    command.downgrade(alembic_cfg, "base")
    assert "success_patterns" not in inspector.get_table_names()
    command.upgrade(alembic_cfg, "head")
    assert "success_patterns" in inspector.get_table_names()
