from __future__ import annotations

import typer

from vibecode.cli.console import print_info, print_success
from vibecode.config.paths import get_vibecode_dir
from vibecode.core.security import ProjectAllowlist


def _get_allowlist() -> ProjectAllowlist:
    return ProjectAllowlist(get_vibecode_dir())


def cmd_project_allow(path: str) -> None:
    allowlist = _get_allowlist()
    allowlist.add(path)
    print_success(f"Added to allowlist: {path}")


def cmd_project_list() -> None:
    allowlist = _get_allowlist()
    projects = allowlist.list()
    if not projects:
        print_info("No projects in allowlist.")
        return
    for p in projects:
        print_info(f"  {p}")


def cmd_project_remove(path: str) -> None:
    allowlist = _get_allowlist()
    allowlist.remove(path)
    print_success(f"Removed from allowlist: {path}")
