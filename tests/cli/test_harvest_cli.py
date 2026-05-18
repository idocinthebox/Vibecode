from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from vibecode.cli import app
from vibecode.core.security import ProjectAllowlist

runner = CliRunner()


def test_cli_harvest_scan_dry_run_prints_summary(tmp_path: Path) -> None:
    base = tmp_path / ".vibecode"
    base.mkdir()
    allowlist = ProjectAllowlist(base)
    allowlist.add(str(tmp_path))

    project = tmp_path / "project"
    project.mkdir()
    (project / "CLAUDE.md").write_text("Always run tests before commit.", encoding="utf-8")

    with patch("vibecode.cli.commands_harvest.get_vibecode_dir", return_value=base):
        result = runner.invoke(app, ["harvest", "scan", "--project", str(project), "--dry-run"])

    assert result.exit_code == 0
    assert "Harvest preview complete" in result.output
    assert "Candidates:" in result.output
