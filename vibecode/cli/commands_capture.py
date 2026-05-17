from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import typer

from vibecode.cli.console import print_error, print_info, print_success
from vibecode.cli.errors import ProjectNotAllowedError
from vibecode.cli.interactive import interactive_capture_failure, interactive_capture_success
from vibecode.config.paths import get_vibecode_dir
from vibecode.core.memory_service import VibeCodeService
from vibecode.core.security import redact_secrets


def _get_service() -> VibeCodeService:
    return VibeCodeService()


def cmd_capture_success(
    project_path: str | None = None,
    name: str | None = None,
    intent: str | None = None,
    language: str | None = None,
    framework: str | None = None,
    files: str | None = None,
    summary: str | None = None,
    original_prompt: str | None = None,
    code_before: str | None = None,
    code_after: str | None = None,
    diff: str | None = None,
    explanation: str | None = None,
    tags: str | None = None,
    source_type: str = "manual",
    source_ref: str | None = None,
    interactive: bool = False,
) -> None:
    service = _get_service()

    if interactive or not (name and intent):
        data = interactive_capture_success()
        project_path = project_path or typer.prompt("Project path", default=str(Path.cwd()))
        name = data["name"]
        intent = data["intent_description"]
        language = data.get("language") or language
        framework = data.get("framework") or framework
        files = data.get("affected_files") or files
        summary = data.get("reasoning_summary") or summary
        original_prompt = data.get("original_prompt") or original_prompt
        code_before = data.get("code_before") or code_before
        code_after = data.get("code_after") or code_after
        tags = data.get("tags") or tags
        source_type = data.get("source_type") or source_type
        source_ref = data.get("source_ref") or source_ref
    else:
        if not project_path:
            print_error("--project is required in non-interactive mode.")
            sys.exit(1)

    if not service.allowlist.is_allowed(project_path):
        raise ProjectNotAllowedError(project_path)

    result = service.capture_success(
        project_path=project_path,
        name=name,
        intent_description=intent,
        language=language,
        framework=framework,
        affected_files=[f.strip() for f in (files or "").split(",") if f.strip()],
        original_prompt=original_prompt or "",
        reasoning_summary=summary or "",
        code_before=code_before or "",
        code_after=code_after or "",
        diff=diff or "",
        explanation=explanation or "",
        tags=[t.strip() for t in (tags or "").split(",") if t.strip()],
        source_type=source_type,
        source_ref=source_ref or "",
    )

    if result.get("created"):
        print_success(f"Captured success pattern: {result['pattern_id']}")
    else:
        print_info(f"Duplicate detected. Existing ID: {result['pattern_id']}")


def cmd_capture_failure(
    project_path: str | None = None,
    task_intent: str | None = None,
    bad_suggestion: str | None = None,
    failure_reason: str | None = None,
    corrected_approach: str | None = None,
    prevention_rule: str | None = None,
    severity: str = "medium",
    language: str | None = None,
    framework: str | None = None,
    files: str | None = None,
    tags: str | None = None,
    source_type: str = "manual",
    source_ref: str | None = None,
    interactive: bool = False,
) -> None:
    service = _get_service()

    if interactive or not (task_intent and bad_suggestion and failure_reason and prevention_rule):
        data = interactive_capture_failure()
        project_path = project_path or typer.prompt("Project path", default=str(Path.cwd()))
        task_intent = data["task_intent"]
        bad_suggestion = data["bad_suggestion"]
        failure_reason = data["failure_reason"]
        corrected_approach = data.get("corrected_approach") or corrected_approach
        prevention_rule = data["prevention_rule"]
        severity = data.get("severity") or severity
        language = data.get("language") or language
        framework = data.get("framework") or framework
        files = data.get("affected_files") or files
        tags = data.get("tags") or tags
        source_type = data.get("source_type") or source_type
        source_ref = data.get("source_ref") or source_ref
    else:
        if not project_path:
            print_error("--project is required in non-interactive mode.")
            sys.exit(1)

    if not service.allowlist.is_allowed(project_path):
        raise ProjectNotAllowedError(project_path)

    result = service.capture_failure(
        project_path=project_path,
        task_intent=task_intent,
        bad_suggestion=bad_suggestion,
        failure_reason=failure_reason,
        prevention_rule=prevention_rule,
        corrected_approach=corrected_approach or "",
        language=language,
        framework=framework,
        affected_files=[f.strip() for f in (files or "").split(",") if f.strip()],
        severity=severity,
        tags=[t.strip() for t in (tags or "").split(",") if t.strip()],
        source_type=source_type,
        source_ref=source_ref or "",
    )

    if result.get("created"):
        print_success(f"Captured failure pattern: {result['failure_id']}")
    else:
        print_info(f"Duplicate detected. Existing ID: {result['failure_id']}")
