from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from vibecode.api.app import create_app


def test_token_report_returns_counts() -> None:
    original_connect = sqlite3.connect

    def _patched_connect(*args, **kwargs):
        kwargs["check_same_thread"] = False
        return original_connect(*args, **kwargs)

    with patch("vibecode.db.sqlite_connection.sqlite3.connect", _patched_connect):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / ".vibecode"
            base.mkdir()
            (base / "success_patterns").mkdir()
            (base / "failure_patterns").mkdir()
            (base / "project_rules").mkdir()
            (base / "agent_profiles").mkdir()
            (base / "config.json").write_text('{"version":"0.1.0"}')

            from vibecode.db.sqlite_connection import get_connection
            from vibecode.db.sqlite_schema import create_schema
            from vibecode.services.capture_service import CaptureService

            conn = get_connection(base)
            create_schema(conn)
            capture = CaptureService(base, conn)
            capture.capture_success(
                {
                    "name": "S",
                    "intent_description": "I",
                    "reasoning_summary": "R",
                }
            )
            capture.capture_failure(
                {
                    "task_intent": "F",
                    "bad_suggestion": "B",
                    "failure_reason": "X",
                    "prevention_rule": "P",
                    "severity": "low",
                }
            )
            capture.add_rule(
                {
                    "rule_text": "R",
                    "rule_type": "architecture",
                    "severity": "low",
                }
            )
            conn.close()

            from vibecode.core.memory_service import VibeCodeService
            fresh_service = VibeCodeService(base)
            with patch("vibecode.api.routes_memory.service", fresh_service):
                client = TestClient(create_app())
                response = client.post("/reports/tokens", json={})
                assert response.status_code == 200
                data = response.json()
                assert data["success_patterns"] == 1
                assert data["failure_patterns"] == 1
                assert data["project_rules"] == 1
            if fresh_service.conn:
                fresh_service.conn.close()
