"""CLI commands for the VibeCode Pro shared databank."""

from __future__ import annotations

import os

import typer

from vibecode.cli.console import print_error, print_info, print_success
from vibecode.config.paths import get_vibecode_dir
from vibecode.integrations.pro_sync import ProSyncAdapter


def _get_adapter() -> ProSyncAdapter:
    endpoint = os.environ.get("VIBECODE_PRO_ENDPOINT", "")
    token = os.environ.get("VIBECODE_PRO_TOKEN", "")
    return ProSyncAdapter(endpoint=endpoint, token=token)


def cmd_pro_share(memory_type: str, memory_id: str, project: str | None) -> None:
    """Share a local pattern with the Pro databank."""
    adapter = _get_adapter()
    if not adapter.is_configured():
        print_error(
            "Pro databank not configured. Set VIBECODE_PRO_ENDPOINT and VIBECODE_PRO_TOKEN environment variables."
        )
        raise typer.Exit(1)

    from vibecode.db.sqlite_connection import get_connection, get_db_path

    base = get_vibecode_dir()
    db_path = get_db_path(base)
    if not db_path.exists():
        print_error("No SQLite database found. Run: vibecode init-db")
        raise typer.Exit(1)

    conn = get_connection(base)
    data: dict = {}
    if memory_type == "failure_pattern":
        row = conn.execute(
            "SELECT * FROM failure_patterns WHERE failure_id = ? AND is_active = 1", (memory_id,)
        ).fetchone()
        if row is None:
            print_error(f"Failure pattern {memory_id!r} not found.")
            conn.close()
            raise typer.Exit(1)
        data = dict(row)
    elif memory_type == "success_pattern":
        row = conn.execute(
            "SELECT * FROM success_patterns WHERE pattern_id = ? AND is_active = 1", (memory_id,)
        ).fetchone()
        if row is None:
            print_error(f"Success pattern {memory_id!r} not found.")
            conn.close()
            raise typer.Exit(1)
        data = dict(row)
    else:
        print_error(f"Unsupported memory type: {memory_type!r}. Use failure_pattern or success_pattern.")
        conn.close()
        raise typer.Exit(1)

    conn.close()

    # Remove internal fields not suitable for sharing
    for key in ("is_active", "content_hash", "agent_source", "source_ref"):
        data.pop(key, None)

    result = adapter.submit(memory_type=memory_type, data=data)
    if "error" in result:
        print_error(f"Share failed: {result['error']}")
        raise typer.Exit(1)

    submission_id = result.get("submission_id", "?")
    print_success(f"Shared {memory_type} {memory_id} → submission_id={submission_id}")


def cmd_pro_retract(submission_id: str) -> None:
    """Retract a previously shared pattern from the Pro databank."""
    adapter = _get_adapter()
    if not adapter.is_configured():
        print_error("Pro databank not configured. Set VIBECODE_PRO_ENDPOINT and VIBECODE_PRO_TOKEN.")
        raise typer.Exit(1)

    result = adapter.retract(submission_id)
    if "error" in result:
        print_error(f"Retract failed: {result['error']}")
        raise typer.Exit(1)

    print_success(f"Retracted submission {submission_id}")


def cmd_pro_status() -> None:
    """Show Pro databank connection status and account info."""
    adapter = _get_adapter()
    if not adapter.is_configured():
        print_info("Pro databank: NOT configured")
        print_info("Set VIBECODE_PRO_ENDPOINT and VIBECODE_PRO_TOKEN to enable.")
        return

    result = adapter.get_status()
    if "error" in result:
        print_error(f"Pro databank unreachable: {result['error']}")
        return

    print_success(f"Pro databank: CONNECTED ({adapter.endpoint})")
    for key, value in result.items():
        if key != "error":
            print_info(f"  {key}: {value}")
