from pathlib import Path

from vibecode.core.prevention_service import PreventionService
from vibecode.db.sqlite_connection import get_connection
from vibecode.db.sqlite_schema import create_schema
from vibecode.services.capture_service import CaptureService


def test_pre_edit_check_returns_failure_matches(temp_base: Path) -> None:
    conn = get_connection(temp_base)
    create_schema(conn)
    capture = CaptureService(temp_base, conn)
    capture.capture_failure(
        {
            "task_intent": "Fix parser",
            "bad_suggestion": "Use eval",
            "failure_reason": "Security issue",
            "prevention_rule": "Do not use eval for parser input",
            "severity": "high",
            "confidence": 0.9,
            "occurrence_count": 3,
            "review_state": "confirmed",
        }
    )

    prevention = PreventionService(temp_base, conn)
    result = prevention.pre_edit_check(
        project_path="/tmp/project",
        file_path="/tmp/project/parser.py",
        language="python",
        proposed_text="eval(user_input)",
        task_intent="Fix parser",
    )

    assert len(result["matches"]) >= 1
    assert "eval" in result["matches"][0]["prevention_rule"].lower()
    assert result["estimated_tokens_saved"] > 0
    conn.close()
