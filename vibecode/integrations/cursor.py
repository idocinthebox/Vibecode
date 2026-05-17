from __future__ import annotations

import json
import shutil
from pathlib import Path


def write_cursor_config(project_root: Path | None = None) -> Path:
    if project_root is None:
        project_root = Path.cwd()
    cursor_dir = project_root / ".cursor"
    cursor_dir.mkdir(parents=True, exist_ok=True)
    config_path = cursor_dir / "mcp.json"

    if config_path.exists():
        backup = cursor_dir / "mcp.json.bak"
        shutil.copy2(config_path, backup)

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
