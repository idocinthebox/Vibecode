"""Pro Databank contribution routes.

POST /databank/contributions   — submit a pattern
DELETE /databank/contributions/{id} — retract a pattern
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from server.pro.db.schema import get_pro_connection
from server.pro.security import require_bearer
from vibecode.core.security import redact_secrets

router = APIRouter(dependencies=[Depends(require_bearer)])

MAX_BODY_BYTES = 64 * 1024


def _redact_data(data: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in data.items():
        out[key] = redact_secrets(value) if isinstance(value, str) else value
    return out


def get_conn():
    """Per-request SQLite connection (dependency injection pattern)."""
    import os
    from pathlib import Path

    data_dir = Path(os.environ.get("PRO_DATA_DIR", ".pro_data"))
    conn = get_pro_connection(data_dir)
    try:
        yield conn
    finally:
        conn.close()


class ContributionRequest(BaseModel):
    memory_type: Literal["success_pattern", "failure_pattern", "project_rule"]
    data: dict[str, Any]
    submitted_by: str = "anonymous"


class ContributionResponse(BaseModel):
    submission_id: str
    memory_type: str
    review_state: str = "pending"
    created: bool = True


@router.post("/databank/contributions", response_model=ContributionResponse)
def submit_contribution(request: ContributionRequest, conn=Depends(get_conn)) -> dict:
    data = _redact_data(request.data)
    body_json = json.dumps(data)
    if len(body_json.encode("utf-8")) > MAX_BODY_BYTES:
        raise HTTPException(status_code=413, detail="Submission too large")

    title = (data.get("name") or data.get("task_intent") or data.get("rule_text", "")[:120] or "Untitled")[:500]
    summary = (data.get("reasoning_summary") or data.get("prevention_rule") or data.get("rule_text", "") or "")[:2000]
    sid = str(uuid.uuid4())

    conn.execute(
        """
        INSERT INTO databank_patterns
            (id, memory_type, title, summary, body_json, language, framework, tags, submitted_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            sid,
            request.memory_type,
            title,
            summary,
            body_json,
            data.get("language", ""),
            data.get("framework", ""),
            json.dumps(data.get("tags", [])),
            request.submitted_by,
        ),
    )
    conn.commit()
    return {"submission_id": sid, "memory_type": request.memory_type, "review_state": "pending", "created": True}


@router.delete("/databank/contributions/{submission_id}")
def retract_contribution(submission_id: str, conn=Depends(get_conn)) -> dict:
    row = conn.execute("SELECT id FROM databank_patterns WHERE id = ?", (submission_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Contribution not found")
    conn.execute("UPDATE databank_patterns SET is_active = 0 WHERE id = ?", (submission_id,))
    conn.commit()
    return {"ok": True, "submission_id": submission_id}
