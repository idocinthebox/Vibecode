from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from vibecode.api.app import create_app


def test_observe_edit_and_diagnostic_creates_pending_failure() -> None:
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

            with patch("vibecode.api.routes_observe.service", fresh_service):
                client = TestClient(create_app())
                edit_resp = client.post(
                    "/observe/edit",
                    json={
                        "event_id": "evt-1",
                        "project_path": tmp,
                        "file_path": str(Path(tmp) / "a.py"),
                        "language": "python",
                        "agent_source": "agent:GitHub.copilot",
                        "range": {
                            "start_line": 0,
                            "start_character": 0,
                            "end_line": 0,
                            "end_character": 0,
                        },
                        "text_before": "a = 1",
                        "text_after": "a = missing",
                        "timestamp": 1000.0,
                        "document_version": 1,
                    },
                )
                assert edit_resp.status_code == 200

                diag_resp = client.post(
                    "/observe/diagnostic",
                    json={
                        "project_path": tmp,
                        "file_path": str(Path(tmp) / "a.py"),
                        "message": "NameError: missing",
                        "severity": "high",
                        "is_new": True,
                        "is_resolved": False,
                        "timestamp": 1001.0,
                    },
                )
                assert diag_resp.status_code == 204

                pending = fresh_service.get_pending_review()
                assert any(item["memory_type"] == "failure_pattern" for item in pending)

            if fresh_service.conn:
                fresh_service.conn.close()
