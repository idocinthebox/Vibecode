__all__ = [
    "Base",
    "create_engine_from_settings",
    "create_schema",
    "get_connection",
    "get_db_path",
    "get_db_session",
    "get_postgres_settings",
    "PostgresSettings",
    "run_migrations",
]


def __getattr__(name: str):
    if name in {"PostgresSettings", "get_postgres_settings"}:
        from vibecode.db.config import PostgresSettings, get_postgres_settings

        return {
            "PostgresSettings": PostgresSettings,
            "get_postgres_settings": get_postgres_settings,
        }[name]
    if name in {"Base"}:
        from vibecode.db.models import Base

        return Base
    if name in {"create_engine_from_settings", "get_db_session"}:
        from vibecode.db.postgres_connection import (
            create_engine_from_settings,
            get_db_session,
        )

        return {
            "create_engine_from_settings": create_engine_from_settings,
            "get_db_session": get_db_session,
        }[name]
    if name in {"get_connection", "get_db_path"}:
        from vibecode.db.sqlite_connection import get_connection, get_db_path

        return {
            "get_connection": get_connection,
            "get_db_path": get_db_path,
        }[name]
    if name == "run_migrations":
        from vibecode.db.sqlite_migrations import run_migrations

        return run_migrations
    if name == "create_schema":
        from vibecode.db.sqlite_schema import create_schema

        return create_schema
    raise AttributeError(name)
