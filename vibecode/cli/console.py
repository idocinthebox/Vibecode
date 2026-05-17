from __future__ import annotations

import os
import sys

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

_console: Console | None = None


def get_console() -> Console:
    global _console
    if _console is None:
        force_terminal = os.environ.get("VIBECODE_FORCE_COLOR", "auto")
        no_color = os.environ.get("NO_COLOR") or os.environ.get("VIBECODE_NO_COLOR")
        _console = Console(
            force_terminal=(force_terminal == "1"),
            no_color=bool(no_color),
            legacy_windows=False,
        )
    return _console


def reset_console() -> None:
    global _console
    _console = None


def _safe_emoji(emoji: str, fallback: str) -> str:
    try:
        emoji.encode(sys.stdout.encoding or "utf-8")
        return emoji
    except UnicodeEncodeError:
        return fallback


def print_success(message: str) -> None:
    console = get_console()
    mark = _safe_emoji("✓", "[OK]")
    console.print(f"[green]{mark}[/green] {message}")


def print_warning(message: str) -> None:
    console = get_console()
    mark = _safe_emoji("⚠", "[!]")
    console.print(f"[yellow]{mark}[/yellow] {message}")


def print_error(message: str) -> None:
    console = get_console()
    mark = _safe_emoji("✗", "[X]")
    console.print(f"[red]{mark}[/red] {message}")


def print_info(message: str) -> None:
    console = get_console()
    mark = _safe_emoji("ℹ", "[i]")
    console.print(f"[blue]{mark}[/blue] {message}")


def print_panel(title: str, content: str, style: str = "blue") -> None:
    console = get_console()
    console.print(Panel(content, title=title, border_style=style))


def print_critical_panel(title: str, content: str) -> None:
    print_panel(title, content, style="red")
