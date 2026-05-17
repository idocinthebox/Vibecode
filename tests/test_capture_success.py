from pathlib import Path

from vibecode.services.capture_service import CaptureService


def test_capture_success_creates_json(temp_base: Path) -> None:
    svc = CaptureService(temp_base)
    pattern, created = svc.capture_success(
        {
            "name": "Test pattern",
            "intent_description": "Test intent",
            "reasoning_summary": "It worked",
        }
    )
    assert created is True
    assert pattern.name == "Test pattern"
    assert svc.success_store.exists(pattern.pattern_id)


def test_duplicate_success_pattern_is_skipped(temp_base: Path) -> None:
    svc = CaptureService(temp_base)
    data = {
        "name": "Dup",
        "intent_description": "Dup intent",
        "reasoning_summary": "Dup summary",
    }
    p1, c1 = svc.capture_success(data)
    assert c1 is True
    p2, c2 = svc.capture_success(data)
    assert c2 is False
    assert p1.pattern_id == p2.pattern_id
