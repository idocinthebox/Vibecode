"""Pro Databank search routes.

POST /databank/search    — keyword search across approved patterns
POST /databank/feedback  — record usefulness feedback
GET  /databank/status    — server and account info
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
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


class SearchRequest(BaseModel):
    query: str
    max_results: int = 10
    memory_type: str | None = None


class FeedbackRequest(BaseModel):
    submission_id: str
    was_useful: bool


@router.post("/databank/search")
def search_databank(request: SearchRequest, conn=Depends(get_conn)) -> dict:
    terms = [t.lower() for t in request.query.split() if t]
    if not terms:
        return {"results": [], "total": 0}

    rows = conn.execute(
        """
        SELECT id, memory_type, title, summary, language, framework, tags,
               usefulness, feedback_count
        FROM databank_patterns
        WHERE is_active = 1 AND review_state = 'approved'
        """,
    ).fetchall()

    scored: list[tuple[float, dict]] = []
    for row in rows:
        text = f"{row['title']} {row['summary']} {row['language']} {row['framework']}".lower()
        score = sum(1 for t in terms if t in text)
        if score:
            scored.append(
                (
                    score + row["usefulness"] * 0.1,
                    {
                        "submission_id": row["id"],
                        "memory_type": row["memory_type"],
                        "title": row["title"],
                        "summary": row["summary"],
                        "language": row["language"],
                        "framework": row["framework"],
                        "usefulness": row["usefulness"],
                        "feedback_count": row["feedback_count"],
                    },
                )
            )

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [item for _, item in scored[: request.max_results]]
    return {"results": results, "total": len(results)}


@router.post("/databank/feedback")
def record_feedback(request: FeedbackRequest, conn=Depends(get_conn)) -> dict:
    import uuid

    row = conn.execute(
        "SELECT id, usefulness, feedback_count FROM databank_patterns WHERE id = ?",
        (request.submission_id,),
    ).fetchone()
    if row is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Submission not found")

    fid = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO databank_feedback (id, pattern_id, was_useful) VALUES (?, ?, ?)",
        (fid, request.submission_id, 1 if request.was_useful else 0),
    )
    # Recalculate usefulness as running average
    new_count = row["feedback_count"] + 1
    new_usefulness = (row["usefulness"] * row["feedback_count"] + (1.0 if request.was_useful else 0.0)) / new_count
    conn.execute(
        "UPDATE databank_patterns SET usefulness = ?, feedback_count = ? WHERE id = ?",
        (new_usefulness, new_count, request.submission_id),
    )
    conn.commit()
    return {"ok": True, "feedback_id": fid}


@router.get("/databank/status")
def databank_status(conn=Depends(get_conn)) -> dict:
    approved = conn.execute(
        "SELECT COUNT(*) AS c FROM databank_patterns WHERE is_active = 1 AND review_state = 'approved'"
    ).fetchone()["c"]
    pending = conn.execute(
        "SELECT COUNT(*) AS c FROM databank_patterns WHERE is_active = 1 AND review_state = 'pending'"
    ).fetchone()["c"]
    return {
        "status": "ok",
        "version": "1.0.0",
        "approved_patterns": approved,
        "pending_patterns": pending,
    }
