from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from vibecode.api.app import create_app
from vibecode.api.routes_memory import get_service as get_memory_service
from vibecode.core.memory_service import VibeCodeService


def test_token_report_returns_counts() -> None:
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

        app = create_app()

        def _override():
            svc = VibeCodeService(base)
            try:
                yield svc
            finally:
                if svc.conn:
                    svc.conn.close()

        app.dependency_overrides[get_memory_service] = _override
        client = TestClient(app)
        response = client.post("/reports/tokens", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["success_patterns"] == 1
        assert data["failure_patterns"] == 1
        assert data["project_rules"] == 1
