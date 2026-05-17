from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from vibecode.mcp.tools import MCPTools

mcp = FastMCP("vibecode")
tools = MCPTools()


@mcp.tool()
def vibecode_search_memory(query: str, project_path: str | None = None, language: str | None = None, max_results: int = 10) -> str:
    """Search VibeCode memory for success patterns, failure patterns, and project rules."""
    return tools.search_memory(query, project_path, language, max_results)


@mcp.tool()
def vibecode_inject_context(query: str, project_path: str | None = None, agent_profile: str = "generic-agent", max_context_tokens: int | None = None) -> str:
    """Generate compact agent context markdown for a given query and profile."""
    return tools.inject_context(query, project_path, agent_profile, max_context_tokens)


@mcp.tool()
def vibecode_capture_success(project_path: str, name: str, intent_description: str, language: str | None = None, framework: str | None = None, affected_files: list[str] | None = None, original_prompt: str | None = None, reasoning_summary: str | None = None, code_before: str | None = None, code_after: str | None = None, diff: str | None = None, explanation: str | None = None, tags: list[str] | None = None, source_type: str = "manual", source_ref: str | None = None) -> str:
    """Capture a success pattern into VibeCode memory."""
    return tools.capture_success(
        project_path=project_path,
        name=name,
        intent_description=intent_description,
        language=language,
        framework=framework,
        affected_files=affected_files or [],
        original_prompt=original_prompt,
        reasoning_summary=reasoning_summary,
        code_before=code_before,
        code_after=code_after,
        diff=diff,
        explanation=explanation,
        tags=tags or [],
        source_type=source_type,
        source_ref=source_ref,
    )


@mcp.tool()
def vibecode_capture_failure(project_path: str, task_intent: str, bad_suggestion: str, failure_reason: str, prevention_rule: str, corrected_approach: str | None = None, language: str | None = None, framework: str | None = None, affected_files: list[str] | None = None, severity: str = "medium", tags: list[str] | None = None, source_type: str = "manual", source_ref: str | None = None) -> str:
    """Capture a failure pattern into VibeCode memory."""
    return tools.capture_failure(
        project_path=project_path,
        task_intent=task_intent,
        bad_suggestion=bad_suggestion,
        failure_reason=failure_reason,
        prevention_rule=prevention_rule,
        corrected_approach=corrected_approach,
        language=language,
        framework=framework,
        affected_files=affected_files or [],
        severity=severity,
        tags=tags or [],
        source_type=source_type,
        source_ref=source_ref,
    )


@mcp.tool()
def vibecode_add_project_rule(project_path: str, rule_text: str, rule_type: str, severity: str = "medium", tags: list[str] | None = None, source_type: str = "manual", source_ref: str | None = None) -> str:
    """Add a project rule to VibeCode memory."""
    return tools.add_project_rule(
        project_path=project_path,
        rule_text=rule_text,
        rule_type=rule_type,
        severity=severity,
        tags=tags or [],
        source_type=source_type,
        source_ref=source_ref,
    )


@mcp.tool()
def vibecode_token_report(project_path: str | None = None, days: int = 30) -> str:
    """Get token savings report from VibeCode memory."""
    return tools.token_report(project_path, days)


@mcp.tool()
def vibecode_health_check() -> str:
    """Check VibeCode service health."""
    return tools.health_check()


def run_mcp_server() -> None:
    mcp.run_stdio_async()
