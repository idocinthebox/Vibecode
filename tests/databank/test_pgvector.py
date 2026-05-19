"""Phase 3 pgvector integration tests against PostgreSQL."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text

from vibecode.db.config import PostgresSettings


def _pg_available() -> bool:
    try:
        settings = PostgresSettings()
        engine = create_engine(settings.url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


PG_AVAILABLE = _pg_available()


@pytest.fixture
def pg_engine():
    if not PG_AVAILABLE:
        pytest.skip("PostgreSQL not available")
    settings = PostgresSettings()
    engine = create_engine(settings.url)
    try:
        yield engine
    finally:
        engine.dispose()


pytestmark = [pytest.mark.pro_server, pytest.mark.skipif(not PG_AVAILABLE, reason="PostgreSQL not available")]


def test_pgvector_embedding_insert_and_nearest_neighbor(pg_engine) -> None:
    with pg_engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS _tmp_pgvector_nn"))
        conn.execute(text("CREATE TABLE _tmp_pgvector_nn (id INT PRIMARY KEY, embedding vector(3))"))
        conn.execute(
            text(
                """
                INSERT INTO _tmp_pgvector_nn (id, embedding)
                VALUES
                    (1, '[1,0,0]'::vector),
                    (2, '[0,1,0]'::vector),
                    (3, '[0,0,1]'::vector)
                """
            )
        )

        nearest = conn.execute(
            text(
                """
                SELECT id
                FROM _tmp_pgvector_nn
                ORDER BY embedding <-> '[0.92,0.08,0]'::vector
                LIMIT 1
                """
            )
        ).scalar()

        assert nearest == 1
