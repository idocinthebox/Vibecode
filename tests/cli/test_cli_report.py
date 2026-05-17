from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from vibecode.cli import app

runner = CliRunner()


def test_cli_report_table_format() -> None:
    original_connect = sqlite3.connect

    def _patched_connect(*args, **kwargs):
        kwargs["check_same_thread"] = False
        return original_connect(*args, **kwargs)

    with patch("vibecode.db.sqlite_connection.sqlite3.connect", _patched_connect):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / ".vibecode"
            base.mkdir()
            (base / "success_patterns").mkdir()
            (base / "failure_patterns").mkdir()
            (base / "project_rules").mkdir()
            (base / "agent_profiles").mkdir()
            (base / "config.json").write_text('{"version":"0.1.0"}')

            from vibecode.db.sqlite_connection import get_connection
            from vibecode.db.sqlite_schema import create_schema
            from vibecode.services.capture_service import CaptureService

            conn = get_connection(base)
            create_schema(conn)
            capture = CaptureService(base, conn)
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
            conn.close()

            with patch("vibecode.cli.commands_report.get_vibecode_dir", return_value=base):
                result = runner.invoke(app, ["report"])
                assert result.exit_code == 0
                assert "Success patterns" in result.output
                assert "Failure patterns" in result.output
                assert "Project rules" in result.output
