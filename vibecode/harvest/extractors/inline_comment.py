from __future__ import annotations

import re
from pathlib import Path

from vibecode.harvest.normalizer import CandidateMemory


class InlineCommentExtractor:
    name = "InlineCommentExtractor"

    _EXTENSIONS = {
        ".c",
        ".cc",
        ".cpp",
        ".cs",
        ".go",
        ".java",
        ".js",
        ".jsx",
        ".kt",
        ".mjs",
        ".php",
        ".py",
        ".rb",
        ".rs",
        ".scala",
        ".sh",
        ".swift",
        ".ts",
        ".tsx",
    }

    _RULE_PATTERN = re.compile(r"(?i)(?:VC-RULE|NOTE\s*rule)\s*:\s*(.+)$")

    @classmethod
    def matches(cls, relative_path: str) -> bool:
        return Path(relative_path).suffix.lower() in cls._EXTENSIONS

    def extract(self, path: Path, relative_path: str) -> list[CandidateMemory]:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        out: list[CandidateMemory] = []

        for idx, line in enumerate(lines, start=1):
            match = self._RULE_PATTERN.search(line)
            if not match:
                continue
            rule = match.group(1).strip()
            if not rule:
                continue

            lowered = rule.lower()
            severity = "medium"
            if any(token in lowered for token in ("must", "never", "do not", "don't")):
                severity = "high"
            elif any(token in lowered for token in ("consider", "may")):
                severity = "low"

            out.append(
                CandidateMemory(
                    memory_type="project_rule",
                    title=rule[:140],
                    rule_text=rule,
                    rule_type="style",
                    severity=severity,
                    source_path=relative_path,
                    line_start=idx,
                    line_end=idx,
                    source_type="harvest:inline_comment",
                    extractor=self.name,
                    signal_strength=0.6,
                )
            )

        return out
