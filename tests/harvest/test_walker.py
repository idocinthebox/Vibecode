from __future__ import annotations

from pathlib import Path

from vibecode.harvest.walker import DocSourceWalker


def test_walker_honors_gitignore_vibecodeignore_size_and_max_files(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    (tmp_path / ".vibecodeignore").write_text("docs/ignore.md\n", encoding="utf-8")

    (tmp_path / "CLAUDE.md").write_text("Always test", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "keep.md").write_text("Prefer small docs", encoding="utf-8")
    (docs / "ignore.md").write_text("Never include me", encoding="utf-8")

    node_modules = tmp_path / "node_modules"
    node_modules.mkdir()
    (node_modules / "lib.md").write_text("ignored", encoding="utf-8")

    # 1MB+ file should be skipped by the walker.
    (docs / "large.md").write_bytes(b"a" * (1_000_001))

    walker = DocSourceWalker()
    files = walker.walk(tmp_path, include=["**/*.md", "CLAUDE.md"], max_files=10)
    rel = {f.relative_to(tmp_path).as_posix() for f in files}

    assert "CLAUDE.md" in rel
    assert "docs/keep.md" in rel
    assert "docs/ignore.md" not in rel
    assert "node_modules/lib.md" not in rel
    assert "docs/large.md" not in rel

    limited = walker.walk(tmp_path, include=["**/*.md", "CLAUDE.md"], max_files=1)
    assert len(limited) == 1
