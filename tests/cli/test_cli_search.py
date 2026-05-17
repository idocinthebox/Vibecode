from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from vibecode.cli import app

runner = CliRunner()


def test_cli_search_outputs_failure_warnings_first() -> None:
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
            capture.capture_failure(
                {
                    "task_intent": "Fix audio",
                    "bad_suggestion": "Use external player",
                    "failure_reason": "User wanted embedded",
                    "prevention_rule": "Do not use external player",
                    "severity": "high",
                    "tags": ["audio"],
                }
            )
            capture.capture_success(
                {
                    "name": "Audio fix",
                    "intent_description": "Fix audio",
                    "reasoning_summary": "Use embedded",
                    "tags": ["audio"],
                }
            )
            conn.close()

            with patch("vibecode.cli.commands_memory.get_vibecode_dir", return_value=base):
                result = runner.invoke(app, ["search", "audio"])
                assert result.exit_code == 0
                # Failure warnings should appear before success patterns
                failure_pos = result.output.find("Failure Warnings")
                success_pos = result.output.find("Success Patterns")
                assert failure_pos != -1
                assert success_pos != -1
                assert failure_pos < success_pos
