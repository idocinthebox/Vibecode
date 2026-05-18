from __future__ import annotations

import re
from pathlib import Path

from vibecode.harvest.normalizer import CandidateMemory


class LinterConfigExtractor:
    name = "LinterConfigExtractor"

    _SUPPORTED = {
        "pyproject.toml",
        ".editorconfig",
        "mypy.ini",
        "ruff.toml",
        ".eslintrc",
        ".eslintrc.js",
        ".eslintrc.cjs",
        ".eslintrc.json",
        ".eslintrc.yaml",
        ".eslintrc.yml",
    }

    @classmethod
    def matches(cls, relative_path: str) -> bool:
        return Path(relative_path).name.lower() in cls._SUPPORTED

    def extract(self, path: Path, relative_path: str) -> list[CandidateMemory]:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        out: list[CandidateMemory] = []

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            setting = self._extract_setting(stripped)
            if not setting:
                continue

            out.append(
                CandidateMemory(
                    memory_type="project_rule",
                    title=f"Linter rule: {setting}"[:140],
                    rule_text=f"Follow configured linting/style rule `{setting}` from {Path(relative_path).name}.",
                    rule_type="style",
                    severity="low",
                    source_path=relative_path,
                    line_start=idx,
                    line_end=idx,
                    source_type="harvest:linter",
                    extractor=self.name,
                    signal_strength=0.55,
                )
            )

            if len(out) >= 30:
                break

        return out

    @staticmethod
    def _extract_setting(line: str) -> str | None:
        if "=" in line:
            left = line.split("=", maxsplit=1)[0].strip().strip("\"'")
            if left:
                return left

        match = re.match(r'"([^"]+)"\s*:\s*', line)
        if match:
            return match.group(1).strip()

        if line.startswith("[") and line.endswith("]"):
            return line.strip("[]")

        return None
