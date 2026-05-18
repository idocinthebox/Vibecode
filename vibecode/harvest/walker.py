from __future__ import annotations

import fnmatch
from pathlib import Path

DEFAULT_INCLUDE_PATTERNS = [
    "CLAUDE.md",
    "AGENTS.md",
    "README.md",
    "CONTRIBUTING.md",
    ".github/copilot-instructions.md",
    ".cursor/rules/**",
    ".windsurfrules",
    ".aider.conf.yml",
    "docs/**",
    "Docs/**",
    "ARCHITECTURE.md",
    "STYLEGUIDE.md",
    "docs/adr/**",
    "*.adr.md",
    "CHANGELOG.md",
    "pyproject.toml",
    ".eslintrc*",
    ".editorconfig",
    "mypy.ini",
    "ruff.toml",
]


class DocSourceWalker:
    def __init__(self, max_file_bytes: int = 1_000_000) -> None:
        self.max_file_bytes = max_file_bytes

    def walk(
        self,
        project_path: str | Path,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        max_files: int = 500,
    ) -> list[Path]:
        root = Path(project_path).resolve()
        include_patterns = include or list(DEFAULT_INCLUDE_PATTERNS)
        ignore_patterns = self._load_ignore_patterns(root)
        ignore_patterns.extend(exclude or [])

        discovered: list[Path] = []
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            if self._is_ignored(rel, ignore_patterns):
                continue
            if not self._is_included(rel, include_patterns):
                continue
            if path.stat().st_size > self.max_file_bytes:
                continue
            if self._is_binary(path):
                continue
            discovered.append(path)
            if len(discovered) >= max_files:
                break
        return discovered

    def _load_ignore_patterns(self, root: Path) -> list[str]:
        patterns: list[str] = []
        for name in (".gitignore", ".vibecodeignore"):
            path = root / name
            if not path.exists():
                continue
            for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                patterns.append(line)
        return patterns

    @staticmethod
    def _is_binary(path: Path) -> bool:
        try:
            chunk = path.read_bytes()[:4096]
        except OSError:
            return True
        return b"\x00" in chunk

    def _is_included(self, rel_path: str, include_patterns: list[str]) -> bool:
        return any(self._matches_pattern(rel_path, pattern) for pattern in include_patterns)

    def _is_ignored(self, rel_path: str, ignore_patterns: list[str]) -> bool:
        ignored = False
        for pattern in ignore_patterns:
            negated = pattern.startswith("!")
            effective = pattern[1:] if negated else pattern
            if self._matches_pattern(rel_path, effective):
                ignored = not negated
        return ignored

    def _matches_pattern(self, rel_path: str, pattern: str) -> bool:
        p = pattern.strip().replace("\\", "/")
        if not p:
            return False
        if p.startswith("./"):
            p = p[2:]
        if p.startswith("/"):
            p = p[1:]

        # Directory patterns like node_modules/
        if p.endswith("/"):
            return rel_path.startswith(p)

        if fnmatch.fnmatch(rel_path, p):
            return True

        # Convenience for bare file names in ignore/include lists.
        if "/" not in p and fnmatch.fnmatch(Path(rel_path).name, p):
            return True

        return False
