from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any


class AuditLogRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def record(
        self,
        actor: str,
        action: str,
        target_type: str,
        target_id: str,
        project_path: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> str:
        entry_id = str(uuid.uuid4())
        ts = datetime.now(timezone.utc).isoformat()
        payload = json.dumps(meta or {})

        self.conn.execute(
            """
            INSERT INTO audit_log (
                id, ts, actor, action, target_type, target_id, project_path, meta
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (entry_id, ts, actor, action, target_type, target_id, project_path, payload),
        )
        self.conn.commit()
        return entry_id

    def list_by_actor(self, actor: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM audit_log WHERE actor = ? ORDER BY ts DESC LIMIT ?",
            (actor, limit),
        ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def list_by_action(self, action: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM audit_log WHERE action = ? ORDER BY ts DESC LIMIT ?",
            (action, limit),
        ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def list_by_target(
        self,
        target_type: str,
        target_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT * FROM audit_log
            WHERE target_type = ? AND target_id = ?
            ORDER BY ts DESC
            LIMIT ?
            """,
            (target_type, target_id, limit),
        ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["meta"] = json.loads(data.get("meta", "{}") or "{}")
        return data
