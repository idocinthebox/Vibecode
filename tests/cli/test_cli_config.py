from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from vibecode.cli import app

runner = CliRunner()


def test_cli_config_show(temp_base: Path) -> None:
    with patch("vibecode.cli.commands_config.ConfigManager") as mock_mgr:
        mock_mgr.return_value.read.return_value = {"general": {"default_storage": "sqlite"}}
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        assert "sqlite" in result.output


def test_cli_config_set(temp_base: Path) -> None:
    with patch("vibecode.cli.commands_config.ConfigManager") as mock_mgr:
        result = runner.invoke(
            app, ["config", "set", "general.default_storage", "json"]
        )
        assert result.exit_code == 0
        mock_mgr.return_value.set.assert_called_once_with(
            "general.default_storage", "json", scope="project"
        )
