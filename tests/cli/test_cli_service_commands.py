from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from vibecode.cli import app

runner = CliRunner()


def test_cli_service_status_handles_not_running(temp_base: Path) -> None:
    with patch("vibecode.cli.commands_service.VibeCodeService") as mock_svc:
        mock_svc.return_value.health_check.return_value = {
            "status": "ok",
            "version": "0.3.0",
            "storage_backend": "json",
            "database_ok": False,
            "allowed_projects_count": 0,
        }
        result = runner.invoke(app, ["service", "status"])
        assert result.exit_code == 0
        assert "status" in result.output.lower()
