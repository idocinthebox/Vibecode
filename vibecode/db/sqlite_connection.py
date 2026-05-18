from __future__ import annotations

import os
import sqlite3
from pathlib import Path


def get_db_path(base_dir: Path | None = None) -> Path:
    env_path = os.environ.get("VIBECODE_DB_PATH")
    if env_path:
        return Path(env_path)
    if base_dir is None:
        base_dir = Path.cwd() / ".vibecode"
    return base_dir / "vibecode.db"


def get_connection(base_dir: Path | None = None) -> sqlite3.Connection:
    db_path = get_db_path(base_dir)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn
