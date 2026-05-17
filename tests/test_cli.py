from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from vibecode.cli import app
from vibecode.services.capture_service import CaptureService

runner = CliRunner()


def test_init_creates_directories(temp_base: Path) -> None:
    with patch("vibecode.cli.commands_init._get_base_dir", return_value=temp_base):
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert (temp_base / "success_patterns").exists()
        assert (temp_base / "failure_patterns").exists()
        assert (temp_base / "project_rules").exists()
        assert (temp_base / "agent_profiles").exists()
        assert (temp_base / "token_reports").exists()
        assert (temp_base / "exports").exists()
        assert (temp_base / "config.json").exists()


def test_init_is_idempotent(temp_base: Path) -> None:
    with patch("vibecode.cli.commands_init._get_base_dir", return_value=temp_base):
        r1 = runner.invoke(app, ["init"])
        assert r1.exit_code == 0
        r2 = runner.invoke(app, ["init"])
        assert r2.exit_code == 0
        assert "already initialized" in r2.output or "Exists" in r2.output


def test_report_counts_memories(temp_base: Path) -> None:
    capture = CaptureService(temp_base)
    capture.capture_success(
        {"name": "S", "intent_description": "I", "reasoning_summary": "R"}
    )
    capture.capture_failure(
        {
            "task_intent": "F",
            "bad_suggestion": "B",
            "failure_reason": "X",
            "prevention_rule": "P",
            "severity": "low",
        }
    )
    capture.add_rule(
        {"rule_text": "R", "rule_type": "architecture", "severity": "low"}
    )

    with patch("vibecode.cli.commands_report.get_vibecode_dir", return_value=temp_base):
        result = runner.invoke(app, ["report"])
        assert result.exit_code == 0
        assert "Success patterns" in result.output
        assert "Failure patterns" in result.output
        assert "Project rules" in result.output
