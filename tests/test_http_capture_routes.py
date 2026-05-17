from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from vibecode.api.app import create_app


def test_capture_success_requires_allowed_project() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / ".vibecode"
        base.mkdir()
        (base / "success_patterns").mkdir()
        (base / "failure_patterns").mkdir()
        (base / "project_rules").mkdir()
        (base / "agent_profiles").mkdir()
        (base / "config.json").write_text('{"version":"0.1.0"}')

        with patch("vibecode.api.routes_memory.service.base_dir", base):
            client = TestClient(create_app())
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
        base = Path(tmp) / ".vibecode"
        base.mkdir()
        (base / "success_patterns").mkdir()
        (base / "failure_patterns").mkdir()
        (base / "project_rules").mkdir()
        (base / "agent_profiles").mkdir()
        (base / "config.json").write_text('{"version":"0.1.0"}')

        with patch("vibecode.api.routes_memory.service.base_dir", base):
            client = TestClient(create_app())
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
        base = Path(tmp) / ".vibecode"
        base.mkdir()
        (base / "success_patterns").mkdir()
        (base / "failure_patterns").mkdir()
        (base / "project_rules").mkdir()
        (base / "agent_profiles").mkdir()
        (base / "config.json").write_text('{"version":"0.1.0"}')

        with patch("vibecode.api.routes_memory.service.base_dir", base):
            client = TestClient(create_app())
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

            from vibecode.core.security import ProjectAllowlist
            allowlist = ProjectAllowlist(base)
            allowlist.add(tmp)

            from vibecode.db.sqlite_connection import get_connection
            from vibecode.db.sqlite_schema import create_schema

            conn = get_connection(base)
            create_schema(conn)
            conn.close()

            from vibecode.core.memory_service import VibeCodeService
            fresh_service = VibeCodeService(base)
            with patch("vibecode.api.routes_memory.service", fresh_service):
                client = TestClient(create_app())
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
            if fresh_service.conn:
                fresh_service.conn.close()
