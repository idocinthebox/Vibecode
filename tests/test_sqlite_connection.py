from __future__ import annotations

import os
from pathlib import Path

from vibecode.db.sqlite_connection import get_connection, get_db_path


def test_get_db_path_defaults_to_vibecode_dir() -> None:
    base = Path("/tmp/fake_vibecode")
    path = get_db_path(base)
    assert path.name == "vibecode.db"
    assert path.parent == base


def test_get_db_path_respects_env_var() -> None:
    custom = "/tmp/custom_vibecode.db"
    os.environ["VIBECODE_DB_PATH"] = custom
    try:
        path = get_db_path()
        # Path normalizes separators on Windows; just verify it ends correctly
        assert str(path).endswith("custom_vibecode.db")
    finally:
        del os.environ["VIBECODE_DB_PATH"]


def test_get_connection_creates_database(temp_base: Path) -> None:
    conn = get_connection(temp_base)
    cursor = conn.execute("SELECT 1")
    assert cursor.fetchone()[0] == 1
    conn.close()
    assert get_db_path(temp_base).exists()
