"""Tests for Phase 5: Extended doctor command."""
from __future__ import annotations

import pytest

from tests.conftest import temp_base


def test_cmd_doctor_runs_without_error(temp_base, monkeypatch) -> None:
    """Doctor should run and return without raising even when DB is missing."""
    import vibecode.config.paths as _paths

    monkeypatch.setattr(_paths, "get_vibecode_dir", lambda: temp_base)

    # Silence output
    import io
    import sys
    captured = io.StringIO()

    from vibecode.cli.commands_doctor import cmd_doctor

    try:
        cmd_doctor()
    except SystemExit:
        pass  # typer.Exit is acceptable


def test_cmd_doctor_includes_harvester_row(temp_base, monkeypatch, capsys) -> None:
    import vibecode.config.paths as _paths
    from vibecode.db.sqlite_connection import get_connection
    from vibecode.db.sqlite_schema import create_schema

    monkeypatch.setattr(_paths, "get_vibecode_dir", lambda: temp_base)
    conn = get_connection(temp_base)
    create_schema(conn)
    conn.close()

    from vibecode.cli.commands_doctor import cmd_doctor

    try:
        cmd_doctor()
    except SystemExit:
        pass

    out = capsys.readouterr().out
    assert "Harvester" in out


def test_cmd_doctor_pro_row_not_configured(temp_base, monkeypatch, capsys) -> None:
    import vibecode.config.paths as _paths

    monkeypatch.setattr(_paths, "get_vibecode_dir", lambda: temp_base)
    monkeypatch.delenv("VIBECODE_PRO_ENDPOINT", raising=False)
    monkeypatch.delenv("VIBECODE_PRO_TOKEN", raising=False)

    from vibecode.cli.commands_doctor import cmd_doctor

    try:
        cmd_doctor()
    except SystemExit:
        pass

    out = capsys.readouterr().out
    assert "Pro databank" in out
