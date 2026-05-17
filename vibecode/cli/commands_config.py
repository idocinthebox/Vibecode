from __future__ import annotations

import json

import typer

from vibecode.cli.config_manager import ConfigManager
from vibecode.cli.console import get_console, print_info, print_success


def cmd_config_show() -> None:
    mgr = ConfigManager()
    data = mgr.read()
    if not data:
        print_info("No config found.")
        return
    console = get_console()
    console.print_json(json.dumps(data))


def cmd_config_set(key: str, value: str, scope: str = "project") -> None:
    mgr = ConfigManager()
    # Try to parse as int/float/bool
    parsed: str | int | float | bool = value
    if value.lower() in ("true", "yes", "on"):
        parsed = True
    elif value.lower() in ("false", "no", "off"):
        parsed = False
    else:
        try:
            if "." in value:
                parsed = float(value)
            else:
                parsed = int(value)
        except ValueError:
            pass
    mgr.set(key, parsed, scope=scope)
    print_success(f"Set {key} = {parsed} ({scope})")


def cmd_config_path() -> None:
    mgr = ConfigManager()
    print_info(mgr.path())
