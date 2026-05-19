"""Pro Databank moderation routes.

GET  /databank/moderation/queue                — list pending patterns
POST /databank/moderation/{id}/approve         — approve a pattern
POST /databank/moderation/{id}/reject          — reject a pattern
POST /databank/moderation/{id}/escalate        — escalate for human review
"""
from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from server.pro.db.schema import get_pro_connection

router = APIRouter()


def get_conn():
    import os
    from pathlib import Path

    data_dir = Path(os.environ.get("PRO_DATA_DIR", ".pro_data"))
    conn = get_pro_connection(data_dir)
    try:
        yield conn
    finally:
        conn.close()


class ModerationActionRequest(BaseModel):
    reason: str = ""
    moderator: str = "system"


@router.get("/databank/moderation/queue")
def moderation_queue(limit: int = 50, conn=Depends(get_conn)) -> dict:
    rows = conn.execute(
        """
        SELECT id, memory_type, title, summary, submitted_by, created_at
        FROM databank_patterns
        WHERE is_active = 1 AND review_state = 'pending'
        ORDER BY created_at ASC
        LIMIT ?
        """,
        (min(limit, 200),),
    ).fetchall()
    return {
        "queue": [dict(row) for row in rows],
        "total": len(rows),
    }


def _moderate(
    pattern_id: str,
    action: Literal["approve", "reject", "escalate"],
    request: ModerationActionRequest,
    conn,
) -> dict:
    row = conn.execute("SELECT id FROM databank_patterns WHERE id = ?", (pattern_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Pattern not found")

    new_state = {"approve": "approved", "reject": "rejected", "escalate": "pending"}.get(action, "pending")
    conn.execute(
        "UPDATE databank_patterns SET review_state = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE id = ?",
        (new_state, pattern_id),
    )
    conn.execute(
        "INSERT INTO moderation_log (id, pattern_id, action, moderator, reason) VALUES (?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), pattern_id, action, request.moderator, request.reason),
    )
    conn.commit()
    return {"ok": True, "pattern_id": pattern_id, "action": action, "new_state": new_state}


@router.post("/databank/moderation/{pattern_id}/approve")
def approve_pattern(
    pattern_id: str, request: ModerationActionRequest, conn=Depends(get_conn)
) -> dict:
    return _moderate(pattern_id, "approve", request, conn)


@router.post("/databank/moderation/{pattern_id}/reject")
def reject_pattern(
    pattern_id: str, request: ModerationActionRequest, conn=Depends(get_conn)
) -> dict:
    return _moderate(pattern_id, "reject", request, conn)


@router.post("/databank/moderation/{pattern_id}/escalate")
def escalate_pattern(
    pattern_id: str, request: ModerationActionRequest, conn=Depends(get_conn)
) -> dict:
    return _moderate(pattern_id, "escalate", request, conn)
