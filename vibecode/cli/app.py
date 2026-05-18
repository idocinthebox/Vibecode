from __future__ import annotations

import typer

from vibecode.cli.commands_capture import cmd_capture_failure, cmd_capture_success
from vibecode.cli.commands_config import cmd_config_path, cmd_config_set, cmd_config_show
from vibecode.cli.commands_doctor import cmd_doctor
from vibecode.cli.commands_export import cmd_export, cmd_import_file
from vibecode.cli.commands_harvest import cmd_harvest_report, cmd_harvest_scan, cmd_harvest_sources
from vibecode.cli.commands_init import (
    cmd_db_status,
    cmd_init,
    cmd_init_db,
    cmd_migrate_json_to_sqlite,
    cmd_status,
)
from vibecode.cli.commands_mcp import (
    cmd_mcp_doctor,
    cmd_mcp_start,
    cmd_mcp_write_antigravity_config,
    cmd_mcp_write_cursor_config,
    cmd_mcp_write_kimi_config,
)
from vibecode.cli.commands_memory import cmd_inject, cmd_search
from vibecode.cli.commands_project import cmd_project_allow, cmd_project_list, cmd_project_remove
from vibecode.cli.commands_report import cmd_report
from vibecode.cli.commands_rules import cmd_add_rule
from vibecode.cli.commands_service import cmd_service_doctor, cmd_service_start, cmd_service_status, cmd_service_stop
from vibecode.cli.completions import install_completion
from vibecode.cli.errors import handle_error

app = typer.Typer(
    name="vibecode",
    help="VibeCode — Local AI Coding Memory",
    no_args_is_help=True,
)

# Sub-typer apps
config_app = typer.Typer(name="config", help="Configuration commands")
service_app = typer.Typer(name="service", help="Local HTTP service commands")
mcp_app = typer.Typer(name="mcp", help="MCP server commands")
project_app = typer.Typer(name="project", help="Project allowlist commands")
harvest_app = typer.Typer(name="harvest", help="Knowledge harvester commands")

app.add_typer(config_app)
app.add_typer(service_app)
app.add_typer(mcp_app)
app.add_typer(project_app)
app.add_typer(harvest_app)


@app.callback()
def main_callback(
    debug: bool = typer.Option(False, "--debug", help="Show full tracebacks on error"),
) -> None:
    """VibeCode CLI."""


# ---------------------------------------------------------------------------
# Top-level commands
# ---------------------------------------------------------------------------


@app.command()
def init() -> None:
    """Initialize VibeCode in the current directory."""
    cmd_init()


@app.command()
def init_db() -> None:
    """Initialize the SQLite database."""
    cmd_init_db()


@app.command("db-status")
def db_status() -> None:
    """Show database status."""
    cmd_db_status()


@app.command("migrate-json-to-sqlite")
def migrate_json_to_sqlite() -> None:
    """Migrate JSON stores to SQLite."""
    cmd_migrate_json_to_sqlite()


@app.command()
def status() -> None:
    """Show VibeCode status."""
    cmd_status()


@app.command()
def doctor() -> None:
    """Run system health checks."""
    cmd_doctor()


@app.command()
def search(
    query: str,
    project: str | None = typer.Option(None, "--project"),
    language: str | None = typer.Option(None, "--language"),
    framework: str | None = typer.Option(None, "--framework"),
    max_results: int = typer.Option(10, "--max-results"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Search memory for patterns, rules, and failures."""
    cmd_search(query, project, language, framework, max_results, json_output)


@app.command()
def inject(
    query: str | None = typer.Argument(None, help="Task query (positional). Alternative to --query."),
    query_opt: str | None = typer.Option(
        None, "--query", help="Task query (named). Alternative to the positional argument."
    ),
    profile: str = typer.Option("generic-agent", "--profile"),
    project: str | None = typer.Option(None, "--project"),
    max_tokens: int | None = typer.Option(None, "--max-tokens"),
    output: str | None = typer.Option(None, "--output"),
    copy: bool = typer.Option(False, "--copy"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Generate agent context markdown for a query."""
    if query and query_opt and query != query_opt:
        typer.echo("Error: pass the query either positionally or via --query, not both.", err=True)
        raise typer.Exit(2)
    resolved = query or query_opt
    if not resolved:
        typer.echo("Error: a query is required (positional or --query).", err=True)
        raise typer.Exit(2)
    cmd_inject(resolved, profile, project, max_tokens, output, copy, json_output)


@app.command("capture-success")
def capture_success(
    project: str | None = typer.Option(None, "--project"),
    name: str | None = typer.Option(None, "--name"),
    intent: str | None = typer.Option(None, "--intent"),
    language: str | None = typer.Option(None, "--language"),
    framework: str | None = typer.Option(None, "--framework"),
    files: str | None = typer.Option(None, "--files"),
    summary: str | None = typer.Option(None, "--summary"),
    original_prompt: str | None = typer.Option(None, "--original-prompt"),
    code_before: str | None = typer.Option(None, "--code-before"),
    code_after: str | None = typer.Option(None, "--code-after"),
    diff: str | None = typer.Option(None, "--diff"),
    explanation: str | None = typer.Option(None, "--explanation"),
    tags: str | None = typer.Option(None, "--tags"),
    source_type: str = typer.Option("manual", "--source-type"),
    source_ref: str | None = typer.Option(None, "--source-ref"),
    interactive: bool = typer.Option(False, "--interactive", "-i"),
) -> None:
    """Capture a success pattern."""
    cmd_capture_success(
        project,
        name,
        intent,
        language,
        framework,
        files,
        summary,
        original_prompt,
        code_before,
        code_after,
        diff,
        explanation,
        tags,
        source_type,
        source_ref,
        interactive,
    )


@app.command("capture-failure")
def capture_failure(
    project: str | None = typer.Option(None, "--project"),
    task_intent: str | None = typer.Option(None, "--task-intent"),
    bad_suggestion: str | None = typer.Option(None, "--bad-suggestion"),
    failure_reason: str | None = typer.Option(None, "--failure-reason"),
    corrected_approach: str | None = typer.Option(None, "--corrected-approach"),
    prevention_rule: str | None = typer.Option(None, "--prevention-rule"),
    severity: str = typer.Option("medium", "--severity"),
    language: str | None = typer.Option(None, "--language"),
    framework: str | None = typer.Option(None, "--framework"),
    files: str | None = typer.Option(None, "--files"),
    tags: str | None = typer.Option(None, "--tags"),
    source_type: str = typer.Option("manual", "--source-type"),
    source_ref: str | None = typer.Option(None, "--source-ref"),
    interactive: bool = typer.Option(False, "--interactive", "-i"),
) -> None:
    """Capture a failure pattern."""
    cmd_capture_failure(
        project,
        task_intent,
        bad_suggestion,
        failure_reason,
        corrected_approach,
        prevention_rule,
        severity,
        language,
        framework,
        files,
        tags,
        source_type,
        source_ref,
        interactive,
    )


@app.command("add-rule")
def add_rule(
    project: str | None = typer.Option(None, "--project"),
    rule_text: str | None = typer.Option(None, "--text"),
    rule_type: str | None = typer.Option(None, "--type"),
    severity: str = typer.Option("medium", "--severity"),
    tags: str | None = typer.Option(None, "--tags"),
    source_type: str = typer.Option("manual", "--source-type"),
    source_ref: str | None = typer.Option(None, "--source-ref"),
    interactive: bool = typer.Option(False, "--interactive", "-i"),
) -> None:
    """Add a project rule."""
    cmd_add_rule(
        project,
        rule_text,
        rule_type,
        severity,
        tags,
        source_type,
        source_ref,
        interactive,
    )


@app.command()
def report(
    days: int = typer.Option(30, "--days"),
    project: str | None = typer.Option(None, "--project"),
    fmt: str = typer.Option("table", "--format"),
    output: str | None = typer.Option(None, "--output"),
) -> None:
    """Generate a memory report."""
    cmd_report(days, project, fmt, output)


@app.command()
def export(
    fmt: str = typer.Option("markdown", "--format"),
    output: str | None = typer.Option(None, "--output"),
) -> None:
    """Export memory to file."""
    cmd_export(fmt, output)


@app.command("import")
def import_file(
    path: str,
    skip_duplicates: bool = typer.Option(True, "--skip-duplicates/--no-skip-duplicates"),
) -> None:
    """Import memory from a JSON file."""
    cmd_import_file(path, skip_duplicates)


@app.command("completion")
def completion_install(
    shell: str = typer.Option(..., "--shell", help="Shell: bash, zsh, powershell"),
) -> None:
    """Install shell completion."""
    install_completion(shell)


# ---------------------------------------------------------------------------
# Config subcommands
# ---------------------------------------------------------------------------


@config_app.command("show")
def config_show() -> None:
    """Show current configuration."""
    cmd_config_show()


@config_app.command("set")
def config_set(
    key: str,
    value: str,
    scope: str = typer.Option("project", "--scope", help="project or user"),
) -> None:
    """Set a configuration value."""
    cmd_config_set(key, value, scope)


@config_app.command("path")
def config_path_cmd() -> None:
    """Show configuration file path."""
    cmd_config_path()


# ---------------------------------------------------------------------------
# Service subcommands
# ---------------------------------------------------------------------------


@service_app.command("start")
def service_start(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8765, "--port"),
) -> None:
    """Start the local HTTP service."""
    cmd_service_start(host, port)


@service_app.command("status")
def service_status() -> None:
    """Check service health."""
    cmd_service_status()


@service_app.command("stop")
def service_stop() -> None:
    """Stop the local service (best-effort)."""
    cmd_service_stop()


@service_app.command("doctor")
def service_doctor() -> None:
    """Run service health checks."""
    cmd_service_doctor()


# ---------------------------------------------------------------------------
# MCP subcommands
# ---------------------------------------------------------------------------


@mcp_app.command("start")
def mcp_start() -> None:
    """Start the MCP server."""
    cmd_mcp_start()


@mcp_app.command("doctor")
def mcp_doctor() -> None:
    """Check MCP setup."""
    cmd_mcp_doctor()


@mcp_app.command("write-cursor-config")
def mcp_write_cursor_config() -> None:
    """Write Cursor MCP configuration."""
    cmd_mcp_write_cursor_config()


@mcp_app.command("write-antigravity-config")
def mcp_write_antigravity_config() -> None:
    """Write Antigravity AGENTS.md configuration."""
    cmd_mcp_write_antigravity_config()


@mcp_app.command("write-kimi-config")
def mcp_write_kimi_config() -> None:
    """Write Kimi MCP configuration."""
    cmd_mcp_write_kimi_config()


# ---------------------------------------------------------------------------
# Project subcommands
# ---------------------------------------------------------------------------


@project_app.command("allow")
def project_allow(path: str) -> None:
    """Allow a project path."""
    cmd_project_allow(path)


@project_app.command("list")
def project_list() -> None:
    """List allowed projects."""
    cmd_project_list()


@project_app.command("remove")
def project_remove(path: str) -> None:
    """Remove a project from the allowlist."""
    cmd_project_remove(path)


# ---------------------------------------------------------------------------
# Harvest subcommands
# ---------------------------------------------------------------------------


@harvest_app.command("scan")
def harvest_scan(
    project: str | None = typer.Option(None, "--project"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    auto_confirm: float = typer.Option(0.8, "--auto-confirm"),
    max_files: int = typer.Option(500, "--max-files"),
    include: list[str] = typer.Option([], "--include"),
    exclude: list[str] = typer.Option([], "--exclude"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Scan project docs and write harvested candidates."""
    cmd_harvest_scan(project, dry_run, auto_confirm, max_files, include, exclude, json_output)


@harvest_app.command("preview")
def harvest_preview(
    project: str | None = typer.Option(None, "--project"),
    auto_confirm: float = typer.Option(0.8, "--auto-confirm"),
    max_files: int = typer.Option(500, "--max-files"),
    include: list[str] = typer.Option([], "--include"),
    exclude: list[str] = typer.Option([], "--exclude"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Preview harvested candidates without writing to memory stores."""
    cmd_harvest_scan(project, True, auto_confirm, max_files, include, exclude, json_output)


@harvest_app.command("report")
def harvest_report(
    report_id: str | None = typer.Option(None, "--id"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Show latest harvest report or a report by id."""
    cmd_harvest_report(report_id, json_output)


@harvest_app.command("sources")
def harvest_sources(
    list_sources: bool = typer.Option(True, "--list"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """List default harvest source patterns."""
    if not list_sources:
        return
    cmd_harvest_sources(json_output)
