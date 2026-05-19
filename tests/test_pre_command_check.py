"""Tests for Phase 8: check_command and recall_on_error service methods."""
from __future__ import annotations

import json
import pytest

from tests.conftest import temp_base


def _make_service(temp_base):
    from vibecode.core.memory_service import VibeCodeService
    from vibecode.db.sqlite_connection import get_connection
    from vibecode.db.sqlite_schema import create_schema

    conn = get_connection(temp_base)
    create_schema(conn)
    conn.close()

    allowlist_path = temp_base / "allowed_projects.json"
    allowlist_path.write_text(json.dumps({"allowed_projects": [str(temp_base)]}))
    return VibeCodeService(base_dir=temp_base)


def _close_service(svc) -> None:
    conn = svc.conn
    if conn is not None:
        conn.close()
        svc._conn = None


def test_check_command_empty_string_returns_no_matches(temp_base) -> None:
    svc = _make_service(temp_base)
    try:
        result = svc.check_command(command="", project_path=str(temp_base))
        assert result["warning_count"] == 0
        assert result["matches"] == []
    finally:
        _close_service(svc)


def test_check_command_no_failures_returns_empty(temp_base) -> None:
    svc = _make_service(temp_base)
    try:
        result = svc.check_command(command="git status", project_path=str(temp_base))
        assert result["warning_count"] == 0
    finally:
        _close_service(svc)


def test_check_command_with_matching_failure_returns_warning(temp_base) -> None:
    svc = _make_service(temp_base)
    try:
        created = svc.capture_failure(
            project_path=str(temp_base),
            task_intent="git push --force to remote branch",
            bad_suggestion="git push --force",
            failure_reason="Force push overwrites remote history",
            prevention_rule="Never use --force unless you own all branches",
            corrected_approach="Use --force-with-lease instead",
            language="git",
            severity="high",
            source_type="manual",
        )
        assert created.get("created") is True

        result = svc.check_command(command="git push --force origin main", project_path=str(temp_base))
        assert isinstance(result["matches"], list)
        assert result["warning_count"] >= 1
    finally:
        _close_service(svc)


def test_recall_on_error_returns_dict_with_results(temp_base) -> None:
    svc = _make_service(temp_base)
    try:
        result = svc.recall_on_error(
            error_output="ModuleNotFoundError: No module named 'httpx'",
            project_path=str(temp_base),
            command="python -m vibecode service start",
        )
        assert "results" in result
        assert isinstance(result["results"], list)
        assert "total" in result
    finally:
        _close_service(svc)


def test_recall_on_error_uses_command_and_error(temp_base) -> None:
    svc = _make_service(temp_base)
    try:
        result = svc.recall_on_error(
            error_output="sqlite3.OperationalError: database is locked",
            project_path=str(temp_base),
            command="pytest tests/",
        )
        assert result["query"]  # query should be non-empty
    finally:
        _close_service(svc)
