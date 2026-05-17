from pathlib import Path

from vibecode.core.auto_capture_service import AutoCaptureService
from vibecode.core.outcome_tracker import TrackedEdit
from vibecode.core.prevention_service import PreventionService
from vibecode.db.sqlite_connection import get_connection
from vibecode.db.sqlite_schema import create_schema
from vibecode.models import EditEvent, EditRange
from vibecode.services.capture_service import CaptureService


def _tracked() -> TrackedEdit:
    edit = EditEvent(
        event_id="e1",
        project_path="/tmp/project",
        file_path="/tmp/project/a.py",
        language="python",
        agent_source="agent:GitHub.copilot",
        range=EditRange(),
        text_before="a = 1",
        text_after="a = missing",
        timestamp=100.0,
        document_version=2,
    )
    tracked = TrackedEdit(
        edit_event=edit,
        deadline_failure_ts=300.0,
        deadline_success_ts=220.0,
    )
    tracked.latest_diagnostic = "NameError: missing"
    tracked.was_reverted = True
    tracked.reverted_to_text = "a = 1"
    return tracked


def test_auto_capture_failure_creates_pending_pattern(temp_base: Path) -> None:
    conn = get_connection(temp_base)
    create_schema(conn)

    capture = CaptureService(temp_base, conn)
    prevention = PreventionService(temp_base, conn)
    auto = AutoCaptureService(capture, prevention, require_review=True)

    result = auto.on_outcome(_tracked(), "failure", 0.86)
    assert result["kind"] == "failure_pattern"
    assert result["created"] is True

    stored = capture.failure_repo.get_by_id(result["memory_id"])
    assert stored is not None
    assert stored.review_state == "pending"
    assert stored.agent_source == "agent:GitHub.copilot"
    assert stored.occurrence_count == 1
    conn.close()
