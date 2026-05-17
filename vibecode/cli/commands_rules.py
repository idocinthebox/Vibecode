from __future__ import annotations

import sys
from pathlib import Path

import typer

from vibecode.cli.console import print_error, print_success
from vibecode.cli.errors import ProjectNotAllowedError
from vibecode.cli.interactive import interactive_add_rule
from vibecode.config.paths import get_vibecode_dir
from vibecode.core.memory_service import VibeCodeService


def cmd_add_rule(
    project_path: str | None = None,
    rule_text: str | None = None,
    rule_type: str | None = None,
    severity: str = "medium",
    tags: str | None = None,
    source_type: str = "manual",
    source_ref: str | None = None,
    interactive: bool = False,
) -> None:
    service = VibeCodeService()

    if interactive or not (rule_text and rule_type):
        data = interactive_add_rule()
        project_path = project_path or typer.prompt("Project path", default=str(Path.cwd()))
        rule_text = data["rule_text"]
        rule_type = data["rule_type"]
        severity = data.get("severity") or severity
        tags = data.get("tags") or tags
        source_type = data.get("source_type") or source_type
        source_ref = data.get("source_ref") or source_ref
    else:
        if not project_path:
            print_error("--project is required in non-interactive mode.")
            sys.exit(1)

    if not service.allowlist.is_allowed(project_path):
        raise ProjectNotAllowedError(project_path)

    result = service.add_project_rule(
        project_path=project_path,
        rule_text=rule_text,
        rule_type=rule_type,
        severity=severity,
        tags=[t.strip() for t in (tags or "").split(",") if t.strip()],
        source_type=source_type,
        source_ref=source_ref or "",
    )
    print_success(f"Added project rule: {result['rule_id']}")
