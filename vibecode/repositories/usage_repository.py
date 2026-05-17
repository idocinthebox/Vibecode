from __future__ import annotations

import sqlite3
from typing import Any


class UsageRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(
        self,
        event_id: str,
        memory_type: str,
        memory_id: str,
        query_text: str | None = None,
        agent_profile: str | None = None,
        tokens_saved: int = 0,
        retrieval_time_ms: int | None = None,
        was_useful: bool | None = None,
        was_modified: bool | None = None,
        created_at: str | None = None,
    ) -> None:
        from datetime import datetime, timezone

        if created_at is None:
            created_at = datetime.now(timezone.utc).isoformat()
        sql = """
        INSERT INTO usage_events (
            event_id, memory_type, memory_id, query_text, agent_profile,
            tokens_saved, retrieval_time_ms, was_useful, was_modified, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(
            sql,
            (
                event_id,
                memory_type,
                memory_id,
                query_text,
                agent_profile,
                tokens_saved,
                retrieval_time_ms,
                1 if was_useful else 0 if was_useful is not None else None,
                1 if was_modified else 0 if was_modified is not None else None,
                created_at,
            ),
        )
        self.conn.commit()

    def list_for_memory(self, memory_type: str, memory_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM usage_events WHERE memory_type = ? AND memory_id = ? ORDER BY created_at DESC",
            (memory_type, memory_id),
        ).fetchall()
        return [dict(r) for r in rows]

    def total_tokens_saved(self) -> int:
        row = self.conn.execute(
            "SELECT COALESCE(SUM(tokens_saved), 0) AS total FROM usage_events"
        ).fetchone()
        return row["total"] if row else 0
