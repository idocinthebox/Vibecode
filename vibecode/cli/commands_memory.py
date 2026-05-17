from __future__ import annotations

import json
from pathlib import Path

import typer

from vibecode.cli.console import get_console, print_info, print_success
from vibecode.cli.formatters import format_inject_preview, format_search_results
from vibecode.config.paths import get_vibecode_dir
from vibecode.core.memory_service import VibeCodeService
from vibecode.db.sqlite_connection import get_connection, get_db_path
from vibecode.services.capture_service import CaptureService
from vibecode.services.injection_service import InjectionService
from vibecode.services.search_service import SearchService


def cmd_search(
    query: str,
    project: str | None = None,
    language: str | None = None,
    framework: str | None = None,
    max_results: int = 10,
    json_output: bool = False,
) -> None:
    base = get_vibecode_dir()
    db_path = get_db_path(base)
    if db_path.exists():
        conn = get_connection(base)
        service = SearchService(base, conn)
        results = service.search(query)
        conn.close()
    else:
        service = SearchService(base)
        results = service.search(query)

    out = []
    for r in results[:max_results]:
        item = {
            "memory_type": r.result_type + "_pattern" if r.result_type in ("success", "failure") else "project_rule",
            "memory_id": r.memory_id,
            "title": r.title,
            "summary": r.summary,
            "why_matched": r.why_matched,
            "severity": r.severity,
            "confidence_score": r.confidence_score,
        }
        if hasattr(r.obj, "source_type"):
            item["source_type"] = r.obj.source_type
        if hasattr(r.obj, "source_ref"):
            item["source_ref"] = r.obj.source_ref
        out.append(item)

    if json_output:
        typer.echo(json.dumps(out, indent=2))
    else:
        format_search_results(out)


def cmd_inject(
    query: str,
    profile: str = "generic-agent",
    project: str | None = None,
    max_tokens: int | None = None,
    output: str | None = None,
    copy: bool = False,
    json_output: bool = False,
) -> None:
    base = get_vibecode_dir()
    db_path = get_db_path(base)
    if db_path.exists():
        conn = get_connection(base)
        capture = CaptureService(base, conn)
        profile_obj = capture.get_profile_by_name(profile)
        if profile_obj is None:
            conn.close()
            print(f"Profile not found: {profile}")
            raise typer.Exit(1)
        service = InjectionService(base, conn)
        markdown = service.inject(query, profile_obj)
        conn.close()
    else:
        capture = CaptureService(base)
        profile_obj = capture.get_profile_by_name(profile)
        if profile_obj is None:
            print(f"Profile not found: {profile}")
            raise typer.Exit(1)
        service = InjectionService(base)
        markdown = service.inject(query, profile_obj)

    from vibecode.services.token_service import TokenService
    tokens = TokenService.estimate_tokens(markdown)

    result = {
        "context_markdown": markdown,
        "estimated_context_tokens": tokens,
        "estimated_tokens_saved": 0,
        "included_counts": {
            "failure_warnings": markdown.count("## Relevant Failure Warnings"),
            "project_rules": markdown.count("## Relevant Project Rules"),
            "success_patterns": markdown.count("## Relevant Success Patterns"),
        },
        "retrieval_time_ms": 0,
    }

    if json_output:
        typer.echo(json.dumps(result, indent=2))
    else:
        format_inject_preview(result)

    if output:
        Path(output).write_text(markdown, encoding="utf-8")
        print_success(f"Context written to {output}")

    if copy:
        try:
            import pyperclip
            pyperclip.copy(markdown)
            print_success("Context copied to clipboard.")
        except ImportError:
            print_info("Install pyperclip for --copy support: pip install pyperclip")
