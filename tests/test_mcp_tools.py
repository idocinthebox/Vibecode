from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

from vibecode.mcp.tools import MCPTools


def test_mcp_search_memory_tool() -> None:
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
                "name": "Test pattern",
                "intent_description": "Test intent",
                "reasoning_summary": "It worked",
                "tags": ["test"],
            }
        )
        conn.close()

        from vibecode.core.memory_service import VibeCodeService
        tools = MCPTools()
        tools.service = VibeCodeService(base)

        result = tools.search_memory("test")
        if tools.service.conn:
            tools.service.conn.close()
        assert len(result["results"]) >= 1


def test_mcp_inject_context_tool() -> None:
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
        capture.seed_profiles()
        conn.close()

        from vibecode.core.memory_service import VibeCodeService
        tools = MCPTools()
        tools.service = VibeCodeService(base)

        result = tools.inject_context("audio", agent_profile="generic-agent")
        if tools.service.conn:
            tools.service.conn.close()
        assert "VibeCode Agent Context" in result["context_markdown"]


def test_mcp_capture_failure_tool() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / ".vibecode"
        base.mkdir()
        (base / "success_patterns").mkdir()
        (base / "failure_patterns").mkdir()
        (base / "project_rules").mkdir()
        (base / "agent_profiles").mkdir()
        (base / "config.json").write_text('{"version":"0.1.0"}')

        # Add to allowlist
        from vibecode.core.security import ProjectAllowlist
        allowlist = ProjectAllowlist(base)
        allowlist.add(tmp)

        from vibecode.db.sqlite_connection import get_connection
        from vibecode.db.sqlite_schema import create_schema

        conn = get_connection(base)
        create_schema(conn)
        conn.close()

        from vibecode.core.memory_service import VibeCodeService
        tools = MCPTools()
        tools.service = VibeCodeService(base)

        result = tools.capture_failure(
            project_path=tmp,
            task_intent="Fix audio",
            bad_suggestion="Use external player",
            failure_reason="User wanted embedded",
            prevention_rule="Do not use external player",
        )
        if tools.service.conn:
            tools.service.conn.close()
        assert "failure_id" in result
