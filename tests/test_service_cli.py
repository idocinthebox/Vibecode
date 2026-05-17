from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from vibecode.cli import app

runner = CliRunner()


def test_service_doctor_reports_checks(temp_base: Path) -> None:
    with patch("vibecode.cli.commands_service.get_vibecode_dir", return_value=temp_base):
        result = runner.invoke(app, ["service", "doctor"])
        assert result.exit_code == 0
        assert ".vibecode exists" in result.output


def test_service_status_shows_health(temp_base: Path) -> None:
    with patch("vibecode.cli.commands_service.get_vibecode_dir", return_value=temp_base):
        result = runner.invoke(app, ["service", "status"])
        assert result.exit_code == 0
        assert "status" in result.output.lower() or "ok" in result.output.lower()
