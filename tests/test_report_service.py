from __future__ import annotations

from pathlib import Path

from vibecode.db.sqlite_connection import get_connection
from vibecode.db.sqlite_schema import create_schema
from vibecode.services.capture_service import CaptureService


def test_report_estimates_token_savings(temp_base: Path) -> None:
    conn = get_connection(temp_base)
    create_schema(conn)
    capture = CaptureService(temp_base, conn)
    capture.capture_success(
        {
            "name": "S1",
            "intent_description": "I1",
            "reasoning_summary": "R1",
            "token_cost_original": 1000,
            "token_cost_retrieval": 200,
        }
    )
    cursor = conn.execute(
        "SELECT SUM(estimated_tokens_saved) AS total FROM success_patterns WHERE is_active = 1"
    )
    total = cursor.fetchone()["total"]
    assert total == 800
    conn.close()
