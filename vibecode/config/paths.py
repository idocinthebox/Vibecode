from __future__ import annotations

import os
from pathlib import Path


def get_vibecode_dir(cwd: Path | None = None) -> Path:
    if cwd is None:
        cwd = Path.cwd()
    return cwd / ".vibecode"


def get_vibecode_logs_dir(cwd: Path | None = None) -> Path:
    d = get_vibecode_dir(cwd) / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d
