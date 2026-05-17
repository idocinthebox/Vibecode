from __future__ import annotations

from typing import Any

import questionary
import typer


def interactive_capture_success() -> dict[str, Any]:
    """Guided interactive prompt for capture-success."""
    data: dict[str, Any] = {}
    data["name"] = questionary.text("Pattern name:").unsafe_ask()
    data["intent_description"] = questionary.text("Intent description:").unsafe_ask()
    data["language"] = questionary.text("Language (optional):", default="").unsafe_ask()
    data["framework"] = questionary.text("Framework (optional):", default="").unsafe_ask()
    data["affected_files"] = questionary.text(
        "Affected files (comma-separated, optional):", default=""
    ).unsafe_ask()
    data["original_prompt"] = questionary.text(
        "Original prompt (optional):", default=""
    ).unsafe_ask()
    data["reasoning_summary"] = questionary.text(
        "Reasoning summary (optional):", default=""
    ).unsafe_ask()
    data["code_before"] = questionary.text("Code before (optional):", default="").unsafe_ask()
    data["code_after"] = questionary.text("Code after (optional):", default="").unsafe_ask()
    data["tags"] = questionary.text("Tags (comma-separated, optional):", default="").unsafe_ask()
    data["source_type"] = questionary.select(
        "Source type:",
        choices=["manual", "cursor", "vscode", "codex", "antigravity", "other"],
        default="manual",
    ).unsafe_ask()
    data["source_ref"] = questionary.text("Source reference (optional):", default="").unsafe_ask()
    return data


def interactive_capture_failure() -> dict[str, Any]:
    """Guided interactive prompt for capture-failure."""
    data: dict[str, Any] = {}
    data["task_intent"] = questionary.text("Task intent:").unsafe_ask()
    data["bad_suggestion"] = questionary.text("Bad suggestion:").unsafe_ask()
    data["failure_reason"] = questionary.text("Why it failed:").unsafe_ask()
    data["corrected_approach"] = questionary.text(
        "Corrected approach (optional):", default=""
    ).unsafe_ask()
    data["prevention_rule"] = questionary.text("Prevention rule:").unsafe_ask()
    data["severity"] = questionary.select(
        "Severity:",
        choices=["low", "medium", "high", "critical"],
        default="medium",
    ).unsafe_ask()
    data["language"] = questionary.text("Language (optional):", default="").unsafe_ask()
    data["framework"] = questionary.text("Framework (optional):", default="").unsafe_ask()
    data["affected_files"] = questionary.text(
        "Affected files (comma-separated, optional):", default=""
    ).unsafe_ask()
    data["tags"] = questionary.text("Tags (comma-separated, optional):", default="").unsafe_ask()
    data["source_type"] = questionary.select(
        "Source type:",
        choices=["manual", "cursor", "vscode", "codex", "antigravity", "other"],
        default="manual",
    ).unsafe_ask()
    data["source_ref"] = questionary.text("Source reference (optional):", default="").unsafe_ask()
    return data


def interactive_add_rule() -> dict[str, Any]:
    """Guided interactive prompt for add-rule."""
    data: dict[str, Any] = {}
    data["rule_text"] = questionary.text("Rule text:").unsafe_ask()
    data["rule_type"] = questionary.text("Rule type (e.g. architecture, dependency):").unsafe_ask()
    data["severity"] = questionary.select(
        "Severity:",
        choices=["low", "medium", "high", "critical"],
        default="medium",
    ).unsafe_ask()
    data["tags"] = questionary.text("Tags (comma-separated, optional):", default="").unsafe_ask()
    data["source_type"] = questionary.select(
        "Source type:",
        choices=["manual", "cursor", "vscode", "codex", "antigravity", "other"],
        default="manual",
    ).unsafe_ask()
    data["source_ref"] = questionary.text("Source reference (optional):", default="").unsafe_ask()
    return data
