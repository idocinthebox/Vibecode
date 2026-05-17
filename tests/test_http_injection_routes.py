from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from vibecode.api.app import create_app


def test_inject_context_prioritizes_failure_warnings() -> None:
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
        capture.capture_failure(
            {
                "task_intent": "Fix audio",
                "bad_suggestion": "Use external player",
                "failure_reason": "User wanted embedded",
                "prevention_rule": "Do not use external player",
                "severity": "high",
                "tags": ["audio"],
            }
        )
        capture.add_rule(
            {
                "rule_text": "Always embed media",
                "rule_type": "ui",
                "severity": "high",
                "tags": ["audio"],
            }
        )
        capture.seed_profiles()
        conn.close()

        with patch("vibecode.api.routes_memory.service.base_dir", base):
            from vibecode.core.memory_service import VibeCodeService
            svc = VibeCodeService(base)
            result = svc.inject_context("audio", agent_profile="generic-agent")
            if svc.conn:
                svc.conn.close()
            assert "VibeCode Agent Context" in result["context_markdown"]
            assert "Relevant Failure Warnings" in result["context_markdown"]
