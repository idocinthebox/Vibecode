from __future__ import annotations

import json
import shutil
from pathlib import Path


def write_kimi_config(project_root: Path | None = None) -> Path:
    """Write Moonshot Kimi MCP configuration to .kimi/mcp.json."""
    if project_root is None:
        project_root = Path.cwd()
    kimi_dir = project_root / ".kimi"
    kimi_dir.mkdir(parents=True, exist_ok=True)
    config_path = kimi_dir / "mcp.json"

    if config_path.exists():
        shutil.copy2(config_path, kimi_dir / "mcp.json.bak")

    config = {
        "mcpServers": {
            "vibecode": {
                "command": "python",
                "args": ["-m", "vibecode.mcp.server"],
                "env": {
                    "VIBECODE_STORAGE_BACKEND": "sqlite",
                },
            }
        }
    }
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return config_path
