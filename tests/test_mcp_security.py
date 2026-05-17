from __future__ import annotations

from vibecode.mcp.tools import MCPTools


def test_mcp_capture_failure_rejects_unallowed_project() -> None:
    tools = MCPTools()
    result = tools.capture_failure(
        project_path="/some/unallowed/path",
        task_intent="Fix thing",
        bad_suggestion="Bad",
        failure_reason="Broke",
        prevention_rule="No",
    )
    import json
    data = json.loads(result)
    assert "error" in data
    assert data["error"] == "PROJECT_NOT_ALLOWED"
