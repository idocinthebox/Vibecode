from __future__ import annotations

import tempfile
from pathlib import Path

from vibecode.mcp.tools import MCPTools


def test_mcp_pre_edit_check_increments_prevention_hits() -> None:
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
        capture.capture_failure(
            {
                "task_intent": "Fix parser",
                "bad_suggestion": "eval(user_input)",
                "failure_reason": "Security issue",
                "prevention_rule": "Do not use eval for parser input",
                "severity": "high",
                "confidence": 0.9,
                "review_state": "confirmed",
            }
        )
        conn.close()

        from vibecode.core.memory_service import VibeCodeService

        tools = MCPTools()
        tools.service = VibeCodeService(base)

        pre = tools.pre_edit_check(
            project_path=tmp,
            file_path=str(Path(tmp) / "parser.py"),
            language="python",
            proposed_text="eval(user_input)",
            task_intent="Fix parser",
        )
        assert len(pre["matches"]) >= 1

        report = tools.token_report(project_path=tmp, days=30)
        assert report["prevention_hits"] >= 1

        if tools.service.conn:
            tools.service.conn.close()
