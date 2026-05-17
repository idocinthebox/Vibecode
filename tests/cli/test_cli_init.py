from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from vibecode.cli import app

runner = CliRunner()


def test_cli_help_runs() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "vibecode" in result.output.lower()


def test_cli_status_runs(temp_base: Path) -> None:
    with patch("vibecode.cli.commands_init._get_base_dir", return_value=temp_base):
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0


def test_cli_doctor_detects_missing_store(temp_base: Path) -> None:
    with patch("vibecode.cli.commands_doctor.get_vibecode_dir", return_value=temp_base):
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 0
        assert ".vibecode folder" in result.output or ".vibecode exists" in result.output
