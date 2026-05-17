from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from vibecode.cli import app

runner = CliRunner()


def test_cli_inject_writes_output_file() -> None:
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
            capture.seed_profiles()
            conn.close()

            output_path = Path(tmp) / "context.md"
            with patch("vibecode.cli.commands_memory.get_vibecode_dir", return_value=base):
                result = runner.invoke(
                    app,
                    ["inject", "--query", "audio", "--profile", "generic-agent", "--output", str(output_path)],
                )
                assert result.exit_code == 0
                assert output_path.exists()
                content = output_path.read_text(encoding="utf-8")
                assert "VibeCode Agent Context" in content
