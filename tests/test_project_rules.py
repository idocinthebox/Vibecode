from pathlib import Path

from vibecode.services.capture_service import CaptureService


def test_add_rule_creates_json(temp_base: Path) -> None:
    svc = CaptureService(temp_base)
    rule = svc.add_rule(
        {
            "rule_text": "No mixing Qt bindings",
            "rule_type": "dependency",
            "severity": "critical",
        }
    )
    assert rule.rule_text == "No mixing Qt bindings"
    assert svc.rule_store.exists(rule.rule_id)
