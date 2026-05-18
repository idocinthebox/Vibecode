from __future__ import annotations

import json
from pathlib import Path

import typer

from vibecode.config.paths import get_vibecode_dir
from vibecode.harvest.service import KnowledgeHarvester


def _resolve_project_path(project: str | None) -> str:
    if project:
        return str(Path(project).resolve())
    return str(Path.cwd().resolve())


def cmd_harvest_scan(
    project: str | None,
    dry_run: bool,
    auto_confirm: float,
    max_files: int,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    json_output: bool = False,
) -> None:
    base = get_vibecode_dir()
    harvester = KnowledgeHarvester(base)
    result = harvester.scan(
        project_path=_resolve_project_path(project),
        include=include or None,
        exclude=exclude or None,
        max_files=max_files,
        auto_confirm_threshold=auto_confirm,
        dry_run=dry_run,
    )
    if "error" in result:
        typer.echo(result["message"], err=True)
        raise typer.Exit(1)

    if json_output:
        typer.echo(json.dumps(result, indent=2))
        return

    mode = "preview" if dry_run else "scan"
    typer.echo(f"Harvest {mode} complete")
    typer.echo(f"Scanned files:       {result['scanned_files']}")
    typer.echo(f"Candidates:          {result['candidates']}")
    typer.echo(f"Auto-confirmed:      {result['auto_confirmed']}")
    typer.echo(f"Queued for review:   {result['queued_for_review']}")
    typer.echo(f"Duplicates skipped:  {result['duplicates_skipped']}")
    typer.echo(f"Report id:           {result['report_id']}")
    typer.echo(f"Report path:         {result['report_path']}")


def cmd_harvest_report(report_id: str | None = None, json_output: bool = False) -> None:
    base = get_vibecode_dir()
    harvester = KnowledgeHarvester(base)
    report = harvester.read_report(report_id)
    if json_output:
        typer.echo(json.dumps(report, indent=2))
        return

    typer.echo("Harvest report")
    typer.echo(f"Report id:           {report.get('report_id', 'none')}")
    typer.echo(f"Scanned files:       {report.get('scanned_files', 0)}")
    typer.echo(f"Candidates:          {report.get('candidates', 0)}")
    typer.echo(f"Auto-confirmed:      {report.get('auto_confirmed', 0)}")
    typer.echo(f"Queued for review:   {report.get('queued_for_review', 0)}")
    typer.echo(f"Duplicates skipped:  {report.get('duplicates_skipped', 0)}")


def cmd_harvest_sources(json_output: bool = False) -> None:
    sources = KnowledgeHarvester.default_sources()
    if json_output:
        typer.echo(json.dumps(sources, indent=2))
        return

    typer.echo("Default harvest sources")
    for source in sources:
        typer.echo(f"- {source}")
