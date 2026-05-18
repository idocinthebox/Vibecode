from __future__ import annotations

import re
from pathlib import Path

from vibecode.harvest.normalizer import CandidateMemory


class ADRExtractor:
    name = "ADRExtractor"

    @staticmethod
    def matches(relative_path: str) -> bool:
        p = relative_path.replace("\\", "/").lower()
        return p.startswith("docs/adr/") or p.endswith(".adr.md")

    def extract(self, path: Path, relative_path: str) -> list[CandidateMemory]:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        status = self._status(lines)
        if status not in {"accepted", "approved"}:
            return []

        decision, start_line, end_line = self._decision_block(lines)
        if not decision:
            return []

        title = decision.split(". ", maxsplit=1)[0][:140]
        return [
            CandidateMemory(
                memory_type="project_rule",
                title=title,
                rule_text=decision,
                rule_type="architecture",
                severity="medium",
                source_path=relative_path,
                line_start=start_line,
                line_end=end_line,
                source_type="harvest:adr",
                extractor=self.name,
                signal_strength=0.85,
            )
        ]

    @staticmethod
    def _status(lines: list[str]) -> str:
        for line in lines:
            match = re.match(r"^\s*status\s*:\s*(.+)$", line, flags=re.IGNORECASE)
            if match:
                return match.group(1).strip().lower()
        return ""

    @staticmethod
    def _decision_block(lines: list[str]) -> tuple[str, int, int]:
        start = -1
        for i, line in enumerate(lines):
            if re.match(r"^\s{0,3}#{1,6}\s+decision\b", line, flags=re.IGNORECASE):
                start = i + 1
                break
        if start < 0:
            return "", 0, 0

        end = len(lines)
        for j in range(start, len(lines)):
            if re.match(r"^\s{0,3}#{1,6}\s+", lines[j]):
                end = j
                break

        block = [line.strip() for line in lines[start:end] if line.strip()]
        decision = " ".join(block)
        return decision.strip(), start + 1, end
