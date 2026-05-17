from __future__ import annotations

import shutil
from pathlib import Path


AGENTS_MD_CONTENT = """# VibeCode Agent Instructions

Use VibeCode MCP tools before major edits:
- `vibecode_search_memory` — search for relevant success/failure patterns and rules
- `vibecode_inject_context` — get compact agent context for your task
- `vibecode_capture_failure` — record regressions and bad suggestions
- `vibecode_capture_success` — record what worked

This helps prevent repeated mistakes and reduces token waste.
"""


def write_agents_md(project_root: Path | None = None) -> Path:
    if project_root is None:
        project_root = Path.cwd()
    path = project_root / "AGENTS.md"

    if path.exists():
        backup = project_root / "AGENTS.md.bak"
        shutil.copy2(path, backup)
        content = path.read_text(encoding="utf-8")
        if "VibeCode" in content:
            return path
        content += "\n\n" + AGENTS_MD_CONTENT
        path.write_text(content, encoding="utf-8")
    else:
        path.write_text(AGENTS_MD_CONTENT, encoding="utf-8")

    return path
