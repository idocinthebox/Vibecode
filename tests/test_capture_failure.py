from pathlib import Path

from vibecode.services.capture_service import CaptureService


def test_capture_failure_creates_json(temp_base: Path) -> None:
    svc = CaptureService(temp_base)
    pattern, created = svc.capture_failure(
        {
            "task_intent": "Fix thing",
            "bad_suggestion": "Bad idea",
            "failure_reason": "It broke",
            "prevention_rule": "Don't do that",
            "severity": "high",
        }
    )
    assert created is True
    assert pattern.task_intent == "Fix thing"
    assert svc.failure_store.exists(pattern.failure_id)


def test_duplicate_failure_pattern_is_skipped(temp_base: Path) -> None:
    svc = CaptureService(temp_base)
    data = {
        "task_intent": "Dup",
        "bad_suggestion": "Bad",
        "failure_reason": "Broke",
        "prevention_rule": "No",
        "severity": "medium",
    }
    p1, c1 = svc.capture_failure(data)
    assert c1 is True
    p2, c2 = svc.capture_failure(data)
    assert c2 is False
    assert p1.failure_id == p2.failure_id
