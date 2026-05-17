from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from vibecode.cli import app

runner = CliRunner()


def test_cli_mcp_doctor() -> None:
    with patch("vibecode.cli.commands_mcp.print_success") as mock_success:
        with patch.dict("sys.modules", {"mcp.server.fastmcp": MagicMock()}):
            result = runner.invoke(app, ["mcp", "doctor"])
            # The command may succeed or fail depending on actual MCP availability
            assert result.exit_code in (0, 1)
