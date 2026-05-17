from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from vibecode.api.app import create_app


def test_review_endpoints_confirm_and_discard() -> None:
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
            from vibecode.services.capture_service import CaptureService

            conn = get_connection(base)
            create_schema(conn)
            capture = CaptureService(base, conn)
            failure, _ = capture.capture_failure(
                {
                    "task_intent": "Fix parser",
                    "bad_suggestion": "eval(user_input)",
                    "failure_reason": "Security issue",
                    "prevention_rule": "Do not use eval",
                    "severity": "high",
                    "review_state": "pending",
                    "source_type": "auto:agent:GitHub.copilot",
                }
            )
            conn.close()

            from vibecode.core.memory_service import VibeCodeService

            fresh_service = VibeCodeService(base)

            with patch("vibecode.api.routes_review.service", fresh_service):
                client = TestClient(create_app())

                pending = client.get("/review/pending")
                assert pending.status_code == 200
                assert len(pending.json()) >= 1

                confirm = client.post(
                    f"/review/{failure.failure_id}/confirm",
                    json={"memory_type": "failure_pattern"},
                )
                assert confirm.status_code == 200
                assert confirm.json().get("ok") is True

                discard = client.post(
                    f"/review/{failure.failure_id}/discard",
                    json={"memory_type": "failure_pattern"},
                )
                assert discard.status_code == 200
                assert discard.json().get("ok") is True

            if fresh_service.conn:
                fresh_service.conn.close()
