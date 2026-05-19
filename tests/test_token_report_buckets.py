"""Tests for Phase 5: Token report with source buckets."""

from __future__ import annotations

import json

import pytest

from tests.conftest import temp_base


def _prepare_service(temp_base):
    from vibecode.core.memory_service import VibeCodeService
    from vibecode.db.sqlite_connection import get_connection
    from vibecode.db.sqlite_schema import create_schema

    conn = get_connection(temp_base)
    create_schema(conn)
    conn.close()

    (temp_base / "allowed_projects.json").write_text(json.dumps({"allowed_projects": [str(temp_base)]}))
    return VibeCodeService(base_dir=temp_base)


def _close_service(svc) -> None:
    conn = svc.conn
    if conn is not None:
        conn.close()
        svc._conn = None


def test_token_report_buckets_all_zeros_on_empty_db(temp_base) -> None:
    svc = _prepare_service(temp_base)
    try:
        report = svc.get_token_report_buckets()
        buckets = report["source_buckets"]
        assert buckets["local"] == 0
        assert buckets["harvested"] == 0
        assert buckets["auto"] == 0
        assert buckets["pro_team"] == 0
        assert buckets["pro_global"] == 0
    finally:
        _close_service(svc)


def test_token_report_buckets_counts_manual_as_local(temp_base) -> None:
    svc = _prepare_service(temp_base)
    try:
        created = svc.capture_success(
            project_path=str(temp_base),
            name="Manual Success",
            intent_description="intent",
            reasoning_summary="summary",
            language="python",
            source_type="manual",
        )
        assert created.get("created") is True

        report = svc.get_token_report_buckets(project_path=str(temp_base))
        assert report["source_buckets"]["local"] >= 1
    finally:
        _close_service(svc)


def test_token_report_buckets_counts_harvest_source(temp_base) -> None:
    svc = _prepare_service(temp_base)
    try:
        created = svc.capture_failure(
            project_path=str(temp_base),
            task_intent="intent",
            bad_suggestion="bad",
            failure_reason="reason",
            prevention_rule="rule",
            language="python",
            severity="medium",
            source_type="harvest:markdown",
        )
        assert created.get("created") is True

        report = svc.get_token_report_buckets(project_path=str(temp_base))
        assert report["source_buckets"]["harvested"] >= 1
    finally:
        _close_service(svc)
