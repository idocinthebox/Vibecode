from __future__ import annotations

from pathlib import Path

from vibecode.db.sqlite_connection import get_connection
from vibecode.db.sqlite_schema import create_schema
from vibecode.services.capture_service import CaptureService
from vibecode.services.search_service import SearchService


def test_search_returns_success_and_failure_matches(temp_base: Path) -> None:
    conn = get_connection(temp_base)
    create_schema(conn)
    capture = CaptureService(temp_base, conn)
    capture.capture_success(
        {
            "name": "PyInstaller Qt fix",
            "intent_description": "Fix Qt conflict",
            "reasoning_summary": "Exclude PyQt5",
            "tags": ["build", "qt"],
        }
    )
    capture.capture_failure(
        {
            "task_intent": "Fix Qt conflict",
            "bad_suggestion": "Use PyQt5",
            "failure_reason": "Conflicts with PySide6",
            "prevention_rule": "Do not use PyQt5 with PySide6",
            "severity": "high",
            "tags": ["qt"],
        }
    )
    capture.add_rule(
        {
            "rule_text": "Use PySide6 only",
            "rule_type": "dependency",
            "severity": "critical",
            "tags": ["qt"],
        }
    )

    search = SearchService(temp_base, conn)
    results = search.search("qt")
    types = [r.result_type for r in results]
    assert "success" in types
    assert "failure" in types
    assert "rule" in types
    conn.close()


def test_search_prioritizes_critical_failures(temp_base: Path) -> None:
    conn = get_connection(temp_base)
    create_schema(conn)
    capture = CaptureService(temp_base, conn)
    capture.capture_success(
        {
            "name": "Low priority success",
            "intent_description": "Success",
            "reasoning_summary": "Works",
            "tags": ["x"],
        }
    )
    capture.capture_failure(
        {
            "task_intent": "Critical issue",
            "bad_suggestion": "Bad",
            "failure_reason": "Broke",
            "prevention_rule": "Never",
            "severity": "critical",
            "tags": ["x"],
        }
    )

    search = SearchService(temp_base, conn)
    results = search.search("x")
    assert results[0].result_type == "failure"
    assert results[0].severity == "critical"
    conn.close()
