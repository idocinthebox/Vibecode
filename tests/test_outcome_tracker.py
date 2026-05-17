from vibecode.core.outcome_tracker import OutcomeTracker
from vibecode.models import DiagnosticSignal, EditEvent, EditRange, RevertSignal


def _event() -> EditEvent:
    return EditEvent(
        event_id="e1",
        project_path="/tmp/project",
        file_path="/tmp/project/a.py",
        language="python",
        agent_source="agent:GitHub.copilot",
        range=EditRange(),
        text_before="x = 1",
        text_after="x = y",
        timestamp=1000.0,
        document_version=2,
    )


def test_outcome_tracker_raises_failure_confidence_on_diagnostic() -> None:
    tracker = OutcomeTracker(min_confidence=0.6)
    tracker.track_edit(_event())

    decisions = tracker.apply_diagnostic(
        DiagnosticSignal(
            project_path="/tmp/project",
            file_path="/tmp/project/a.py",
            message="NameError",
            severity="high",
            is_new=True,
            is_resolved=False,
            timestamp=1005.0,
        )
    )

    assert len(decisions) == 1
    assert decisions[0].kind == "failure"
    assert decisions[0].confidence >= 0.6


def test_outcome_tracker_marks_revert_as_strong_failure() -> None:
    tracker = OutcomeTracker(min_confidence=0.6)
    tracker.track_edit(_event())

    decisions = tracker.apply_revert(
        RevertSignal(
            project_path="/tmp/project",
            event_id="e1",
            reverted_to_text="x = 1",
            timestamp=1010.0,
        )
    )

    assert len(decisions) == 1
    assert decisions[0].kind == "failure"
    assert decisions[0].confidence >= 0.9
