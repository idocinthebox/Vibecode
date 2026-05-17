from __future__ import annotations

from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from vibecode.db.config import PostgresSettings, get_postgres_settings


def create_engine_from_settings(settings: PostgresSettings | None = None) -> Any:
    settings = settings or get_postgres_settings()
    return create_engine(
        settings.url,
        pool_pre_ping=True,
        echo=False,
    )


def get_sessionmaker(settings: PostgresSettings | None = None) -> sessionmaker:
    engine = create_engine_from_settings(settings)
    return sessionmaker(bind=engine, expire_on_commit=False)


def get_db_session(settings: PostgresSettings | None = None) -> Session:
    SessionLocal = get_sessionmaker(settings)
    return SessionLocal()
