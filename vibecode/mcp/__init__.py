__all__ = ["run_mcp_server"]


def __getattr__(name: str):
    if name == "run_mcp_server":
        from vibecode.mcp.server import run_mcp_server

        return run_mcp_server
    raise AttributeError(name)
