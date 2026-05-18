from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from vibecode.api.app import create_app
from vibecode.api.routes_memory import get_service as get_memory_service
from vibecode.core.memory_service import VibeCodeService


def _setup_base(tmp: str) -> Path:
    base = Path(tmp) / ".vibecode"
    base.mkdir()
    (base / "success_patterns").mkdir()
    (base / "failure_patterns").mkdir()
    (base / "project_rules").mkdir()
    (base / "agent_profiles").mkdir()
    (base / "config.json").write_text('{"version":"0.1.0"}')
    return base


def _client_for(base: Path) -> TestClient:
    def _override():
        svc = VibeCodeService(base)
        try:
            yield svc
        finally:
            if svc.conn:
                svc.conn.close()

    app = create_app()
    app.dependency_overrides[get_memory_service] = _override
    return TestClient(app)


def test_capture_success_requires_allowed_project() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = _setup_base(tmp)
        client = _client_for(base)
        response = client.post(
            "/memory/capture-success",
            json={
                "project_path": "/some/unallowed/project",
                "name": "Test",
                "intent_description": "Intent",
            },
        )
        assert response.status_code == 403
        assert "PROJECT_NOT_ALLOWED" in response.text


def test_capture_failure_requires_allowed_project() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = _setup_base(tmp)
        client = _client_for(base)
        response = client.post(
            "/memory/capture-failure",
            json={
                "project_path": "/some/unallowed/project",
                "task_intent": "Fix thing",
                "bad_suggestion": "Bad",
                "failure_reason": "Broke",
                "prevention_rule": "No",
            },
        )
        assert response.status_code == 403
        assert "PROJECT_NOT_ALLOWED" in response.text


def test_add_rule_requires_allowed_project() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = _setup_base(tmp)
        client = _client_for(base)
        response = client.post(
            "/rules/add",
            json={
                "project_path": "/some/unallowed/project",
                "rule_text": "Rule",
                "rule_type": "dependency",
            },
        )
        assert response.status_code == 403
        assert "PROJECT_NOT_ALLOWED" in response.text


def test_capture_success_with_allowed_project() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = _setup_base(tmp)

        from vibecode.core.security import ProjectAllowlist

        allowlist = ProjectAllowlist(base)
        allowlist.add(tmp)

        from vibecode.db.sqlite_connection import get_connection
        from vibecode.db.sqlite_schema import create_schema

        conn = get_connection(base)
        create_schema(conn)
        conn.close()

        client = _client_for(base)
        response = client.post(
            "/memory/capture-success",
            json={
                "project_path": tmp,
                "name": "Test",
                "intent_description": "Intent",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "pattern_id" in data
        assert data["created"] is True
