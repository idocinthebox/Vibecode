from __future__ import annotations

import json
from typing import Any

from rich import box
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from vibecode.cli.console import get_console


def format_search_results(results: list[dict[str, Any]], max_width: int = 100) -> None:
    console = get_console()
    failures = [r for r in results if r.get("memory_type") == "failure_pattern"]
    rules = [r for r in results if r.get("memory_type") == "project_rule"]
    successes = [r for r in results if r.get("memory_type") == "success_pattern"]

    if failures:
        console.print("\n[bold red]Failure Warnings[/bold red]")
        for r in failures:
            severity = r.get("severity", "medium") or "medium"
            style = "red" if severity in ("critical", "high") else "yellow"
            console.print(
                Panel(
                    f"{r.get('summary', '')}\n\n[dim]Why matched:[/dim] {r.get('why_matched', '')}",
                    title=f"[{severity.upper()}] {r.get('title', 'Unknown')}",
                    border_style=style,
                )
            )

    if rules:
        console.print("\n[bold cyan]Project Rules[/bold cyan]")
        for r in rules:
            severity = r.get("severity", "medium") or "medium"
            console.print(
                Panel(
                    f"{r.get('summary', '')}\n\n[dim]Why matched:[/dim] {r.get('why_matched', '')}",
                    title=f"[{severity.upper()}] {r.get('title', 'Unknown')}",
                    border_style="cyan",
                )
            )

    if successes:
        console.print("\n[bold green]Success Patterns[/bold green]")
        for r in successes:
            console.print(
                Panel(
                    f"{r.get('summary', '')}\n\n[dim]Why matched:[/dim] {r.get('why_matched', '')}",
                    title=r.get("title", "Unknown"),
                    border_style="green",
                )
            )

    if not any([failures, rules, successes]):
        console.print("[dim]No results found.[/dim]")


def format_inject_preview(result: dict[str, Any]) -> None:
    console = get_console()
    md = result.get("context_markdown", "")
    tokens = result.get("estimated_context_tokens", 0)
    saved = result.get("estimated_tokens_saved", 0)
    counts = result.get("included_counts", {})

    table = Table(show_header=False, box=box.SIMPLE)
    table.add_row("Context tokens", str(tokens))
    table.add_row("Tokens saved", str(saved))
    table.add_row("Failure warnings", str(counts.get("failure_warnings", 0)))
    table.add_row("Project rules", str(counts.get("project_rules", 0)))
    table.add_row("Success patterns", str(counts.get("success_patterns", 0)))
    console.print(table)
    console.print("")
    console.print(Markdown(md))


def format_report(data: dict[str, Any], fmt: str = "table") -> str:
    if fmt == "json":
        return json.dumps(data, indent=2)

    if fmt == "markdown":
        lines = [
            "# VibeCode Report",
            "",
            f"- **Success patterns:** {data.get('success_patterns', 0)}",
            f"- **Failure patterns:** {data.get('failure_patterns', 0)}",
            f"- **Project rules:** {data.get('project_rules', 0)}",
            f"- **Estimated tokens saved:** {data.get('estimated_tokens_saved', 0)}",
            "",
        ]
        if data.get("most_used"):
            lines.append("## Most Used Patterns")
            for name, usage in data["most_used"]:
                lines.append(f"- {name} ({usage} uses)")
            lines.append("")
        if data.get("highest_severity"):
            lines.append("## Highest Severity Failures")
            for sev, intent in data["highest_severity"]:
                lines.append(f"- [{sev.upper()}] {intent}")
            lines.append("")
        return "\n".join(lines)

    # table
    console = get_console()
    table = Table(title="VibeCode Report", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_row("Success patterns", str(data.get("success_patterns", 0)))
    table.add_row("Failure patterns", str(data.get("failure_patterns", 0)))
    table.add_row("Project rules", str(data.get("project_rules", 0)))
    table.add_row("Tokens saved", str(data.get("estimated_tokens_saved", 0)))
    console.print(table)

    if data.get("most_used"):
        console.print("\n[bold]Most used patterns:[/bold]")
        for name, usage in data["most_used"]:
            console.print(f"  - {name} ({usage} uses)")
    if data.get("highest_severity"):
        console.print("\n[bold]Highest severity failures:[/bold]")
        for sev, intent in data["highest_severity"]:
            console.print(f"  - [{sev.upper()}] {intent}")
    return ""


def format_doctor_report(checks: list[dict[str, Any]]) -> None:
    console = get_console()
    ok_count = sum(1 for c in checks if c["status"] == "OK")
    warn_count = sum(1 for c in checks if c["status"] == "WARNING")
    err_count = sum(1 for c in checks if c["status"] == "ERROR")

    table = Table(title="VibeCode Doctor", box=box.ROUNDED)
    table.add_column("Status", style="bold")
    table.add_column("Check", style="cyan")
    table.add_column("Detail", style="dim")

    for c in checks:
        status = c["status"]
        if status == "OK":
            status_text = "[green]✓ OK[/green]"
        elif status == "WARNING":
            status_text = "[yellow]⚠ WARNING[/yellow]"
        else:
            status_text = "[red]✗ ERROR[/red]"
        table.add_row(status_text, c["name"], c.get("detail", ""))

    console.print(table)
    console.print("")
    console.print(f"[green]{ok_count} OK[/green]  [yellow]{warn_count} Warning[/yellow]  [red]{err_count} Error[/red]")

    fixes = [c for c in checks if c.get("fix")]
    if fixes:
        console.print("\n[bold]Suggested fixes:[/bold]")
        for c in fixes:
            console.print(f"  {c['name']}: {c['fix']}")
