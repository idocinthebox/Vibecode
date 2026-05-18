from __future__ import annotations

import re
from pathlib import Path

from vibecode.harvest.normalizer import CandidateMemory

_IMPERATIVE_PREFIXES = (
    "always",
    "never",
    "do not",
    "don't",
    "prefer",
    "use ",
    "required:",
    "must",
)


class ClaudeMdExtractor:
    name = "ClaudeMdExtractor"

    @staticmethod
    def matches(relative_path: str) -> bool:
        p = relative_path.replace("\\", "/").lower()
        special = {
            "claude.md",
            "agents.md",
            ".github/copilot-instructions.md",
        }
        if p in special:
            return True
        if p.startswith(".cursor/rules/"):
            return True
        return False

    def extract(self, path: Path, relative_path: str) -> list[CandidateMemory]:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        out: list[CandidateMemory] = []
        for i, line in enumerate(lines, start=1):
            cleaned = self._clean_rule_line(line)
            if not cleaned:
                continue
            if cleaned.startswith("#"):
                continue
            if not self._looks_imperative(cleaned):
                continue
            severity = self._severity(cleaned)
            out.append(
                CandidateMemory(
                    memory_type="project_rule",
                    title=cleaned[:140],
                    rule_text=cleaned,
                    rule_type="agent_behavior",
                    severity=severity,
                    source_path=relative_path,
                    line_start=i,
                    line_end=i,
                    source_type="harvest:claude_md",
                    extractor=self.name,
                    signal_strength=0.85 if ":" in cleaned else 0.7,
                )
            )
        return out

    @staticmethod
    def _clean_rule_line(line: str) -> str:
        stripped = line.strip()
        if not stripped:
            return ""
        stripped = re.sub(r"^[-*]\s+", "", stripped)
        stripped = re.sub(r"^\d+\.\s+", "", stripped)
        return stripped.strip()

    @staticmethod
    def _looks_imperative(text: str) -> bool:
        lower = text.lower()
        return any(lower.startswith(prefix) for prefix in _IMPERATIVE_PREFIXES)

    @staticmethod
    def _severity(text: str) -> str:
        lower = text.lower()
        if lower.startswith("never") or lower.startswith("must") or lower.startswith("do not"):
            return "high"
        if lower.startswith("required:"):
            return "high"
        if lower.startswith("prefer"):
            return "medium"
        return "medium"
