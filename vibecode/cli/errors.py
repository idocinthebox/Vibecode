from __future__ import annotations

import sys
import traceback

from vibecode.cli.console import get_console, print_error


class CLIError(Exception):
    """Base exception for CLI errors with user-friendly messages."""

    def __init__(self, message: str, fix: str = "", exit_code: int = 1) -> None:
        super().__init__(message)
        self.message = message
        self.fix = fix
        self.exit_code = exit_code


class StorageNotInitializedError(CLIError):
    def __init__(self) -> None:
        super().__init__(
            message="VibeCode storage is not initialized.",
            fix="Run: vibecode init\n       vibecode init-db",
            exit_code=1,
        )


class ProjectNotAllowedError(CLIError):
    def __init__(self, path: str) -> None:
        super().__init__(
            message=f"Project path is not in the allowlist: {path}",
            fix=f"Run: vibecode project allow {path}",
            exit_code=1,
        )


class ServiceNotRunningError(CLIError):
    def __init__(self) -> None:
        super().__init__(
            message="VibeCode local service is not running.",
            fix="Run: vibecode service start",
            exit_code=1,
        )


def handle_error(err: Exception, debug: bool = False) -> None:
    console = get_console()
    if isinstance(err, CLIError):
        print_error(err.message)
        if err.fix:
            console.print(f"\n[bold]Fix:[/bold]")
            console.print(f"  {err.fix}")
        sys.exit(err.exit_code)
    else:
        print_error(f"Unexpected error: {err}")
        if debug:
            console.print("\n[dim]Traceback:[/dim]")
            console.print(traceback.format_exc())
        sys.exit(1)
