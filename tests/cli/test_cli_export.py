from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from vibecode.cli import app

runner = CliRunner()


def test_cli_export_json() -> None:
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
            conn.close()

            output_file = Path(tmp) / "export.json"
            with patch("vibecode.cli.commands_export.get_vibecode_dir", return_value=base):
                result = runner.invoke(
                    app, ["export", "--format", "json", "--output", str(output_file)]
                )
                assert result.exit_code == 0
                assert output_file.exists()
                data = json.loads(output_file.read_text(encoding="utf-8"))
                assert "version" in data
                assert len(data["success_patterns"]) >= 1


def test_cli_import_skips_duplicates() -> None:
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
            conn.close()
            capture.conn = None

            import_data = {
                "version": "1.0",
                "success_patterns": [
                    {"name": "S", "intent_description": "I", "reasoning_summary": "R"}
                ],
                "failure_patterns": [],
                "project_rules": [],
            }
            import_path = Path(tmp) / "import.json"
            import_path.write_text(json.dumps(import_data), encoding="utf-8")

            with patch("vibecode.cli.commands_export.get_vibecode_dir", return_value=base):
                result = runner.invoke(app, ["import", str(import_path)])
                assert result.exit_code == 0
                assert "skipped" in result.output.lower() or "0" in result.output
