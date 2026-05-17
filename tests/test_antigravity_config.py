from __future__ import annotations

import tempfile
from pathlib import Path

from vibecode.integrations.antigravity import write_agents_md


def test_antigravity_agents_md_generation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        path = write_agents_md(root)
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "VibeCode" in content
        assert "vibecode_search_memory" in content
