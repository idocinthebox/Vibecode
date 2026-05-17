from __future__ import annotations

import tempfile
from pathlib import Path

from vibecode.core.security import ProjectAllowlist


def test_project_allowlist_add_and_list() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / ".vibecode"
        base.mkdir()
        allowlist = ProjectAllowlist(base)
        allowlist.add("/fake/project")
        resolved = str(Path("/fake/project").resolve())
        assert resolved in allowlist.list()


def test_project_allowlist_remove() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / ".vibecode"
        base.mkdir()
        allowlist = ProjectAllowlist(base)
        allowlist.add("/fake/project")
        allowlist.remove("/fake/project")
        assert "/fake/project" not in allowlist.list()


def test_project_allowlist_is_allowed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / ".vibecode"
        base.mkdir()
        allowlist = ProjectAllowlist(base)
        allowlist.add(str(tmp))
        assert allowlist.is_allowed(str(tmp)) is True
        assert allowlist.is_allowed(str(Path(tmp) / "subdir")) is True
        assert allowlist.is_allowed("/other/path") is False
