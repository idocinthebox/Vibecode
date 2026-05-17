from pathlib import Path

from vibecode.services.capture_service import CaptureService
from vibecode.services.export_service import ExportService


def test_export_memory_creates_markdown_files(temp_base: Path) -> None:
    capture = CaptureService(temp_base)
    capture.capture_success(
        {
            "name": "S1",
            "intent_description": "Intent",
            "reasoning_summary": "Summary",
        }
    )
    capture.capture_failure(
        {
            "task_intent": "F1",
            "bad_suggestion": "Bad",
            "failure_reason": "Broke",
            "prevention_rule": "No",
            "severity": "medium",
        }
    )
    capture.add_rule(
        {
            "rule_text": "R1",
            "rule_type": "architecture",
            "severity": "low",
        }
    )

    export = ExportService(temp_base)
    paths = export.export_all()
    names = {p.name for p in paths}
    assert "PROJECT_MEMORY.md" in names
    assert "FAILURE_BANK.md" in names
    assert "PROJECT_RULES.md" in names
    assert "AGENT_CONTEXT_SUMMARY.md" in names

    for p in paths:
        assert p.exists()
        content = p.read_text(encoding="utf-8")
        assert len(content) > 0
