from __future__ import annotations

import tempfile
from pathlib import Path

from vibecode.api.app import create_app  # noqa: F401  (keeps import surface stable)


def test_search_memory_returns_success_failure_and_rules() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / ".vibecode"
        base.mkdir()
        (base / "success_patterns").mkdir()
        (base / "failure_patterns").mkdir()
        (base / "project_rules").mkdir()
        (base / "agent_profiles").mkdir()
        (base / "config.json").write_text('{"version":"0.1.0"}')

        # Seed data via SQLite
        from vibecode.db.sqlite_connection import get_connection
        from vibecode.db.sqlite_schema import create_schema
        from vibecode.services.capture_service import CaptureService

        conn = get_connection(base)
        create_schema(conn)
        capture = CaptureService(base, conn)
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
        conn.close()

        from vibecode.core.memory_service import VibeCodeService

        svc = VibeCodeService(base)
        result = svc.search_memory("qt", max_results=10)
        if svc.conn:
            svc.conn.close()
        types = [r["memory_type"] for r in result["results"]]
        assert "success_pattern" in types
        assert "failure_pattern" in types
        assert "project_rule" in types
