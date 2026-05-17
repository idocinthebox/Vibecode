from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from vibecode.db.config import PostgresSettings
from vibecode.db.models import Base


def _pg_available() -> bool:
    try:
        settings = PostgresSettings()
        engine = create_engine(settings.url, pool_pre_ping=True, connect_args={"connect_timeout": 3})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


PG_AVAILABLE = _pg_available()


@pytest.fixture(scope="session")
def pg_engine():
    if not PG_AVAILABLE:
        pytest.skip("PostgreSQL not available")
    settings = PostgresSettings()
    engine = create_engine(settings.url, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def pg_session(pg_engine):
    connection = pg_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    # Create all tables for this test transaction
    Base.metadata.create_all(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
