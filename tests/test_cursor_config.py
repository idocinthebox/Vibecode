from __future__ import annotations

import tempfile
from pathlib import Path

from vibecode.integrations.cursor import write_cursor_config


def test_cursor_config_generation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        path = write_cursor_config(root)
        assert path.exists()
        import json
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "mcpServers" in data
        assert "vibecode" in data["mcpServers"]
