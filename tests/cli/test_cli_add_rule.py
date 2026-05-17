from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from vibecode.cli import app

runner = CliRunner()


def test_cli_add_rule_non_interactive() -> None:
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

            from vibecode.core.security import ProjectAllowlist
            allowlist = ProjectAllowlist(base)
            allowlist.add(tmp)

            from vibecode.db.sqlite_connection import get_connection
            from vibecode.db.sqlite_schema import create_schema

            conn = get_connection(base)
            create_schema(conn)
            conn.close()

            with patch("vibecode.cli.commands_rules.VibeCodeService") as mock_svc_cls:
                from vibecode.core.memory_service import VibeCodeService
                svc = VibeCodeService(base)
                mock_svc_cls.return_value = svc
                result = runner.invoke(
                    app,
                    [
                        "add-rule",
                        "--project", tmp,
                        "--text", "Use PySide6 only",
                        "--type", "dependency",
                    ],
                )
                if svc.conn:
                    svc.conn.close()
                assert result.exit_code == 0
                assert "Added project rule" in result.output
