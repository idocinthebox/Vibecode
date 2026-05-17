from __future__ import annotations

import typer

from vibecode.cli.console import print_error, print_info, print_success


def cmd_mcp_start() -> None:
    from vibecode.mcp.server import run_mcp_server

    print_info("Starting VibeCode MCP server (stdio)...")
    import asyncio
    asyncio.run(run_mcp_server())


def cmd_mcp_doctor() -> None:
    try:
        from mcp.server.fastmcp import FastMCP
        print_success("MCP SDK: OK")
    except ImportError:
        print_error("MCP SDK: NOT INSTALLED")
        raise typer.Exit(1)
    try:
        from vibecode.mcp.server import mcp
        tools = [t.name for t in mcp._tool_manager._tools.values()]
        print_info(f"MCP tools registered: {len(tools)}")
        for t in tools:
            print_info(f"  - {t}")
    except Exception as e:
        print_error(f"MCP tool load error: {e}")
        raise typer.Exit(1)


def cmd_mcp_write_cursor_config() -> None:
    from vibecode.integrations.cursor import write_cursor_config
    path = write_cursor_config()
    print_success(f"Cursor MCP config written: {path}")


def cmd_mcp_write_antigravity_config() -> None:
    from vibecode.integrations.antigravity import write_agents_md
    path = write_agents_md()
    print_success(f"Antigravity AGENTS.md written: {path}")
