from __future__ import annotations

import re
from pathlib import Path

from vibecode.harvest.normalizer import CandidateMemory


class ChangelogFixExtractor:
    name = "ChangelogFixExtractor"

    @staticmethod
    def matches(relative_path: str) -> bool:
        return Path(relative_path).name.lower() == "changelog.md"

    def extract(self, path: Path, relative_path: str) -> list[CandidateMemory]:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        sections = self._sections(lines)
        out: list[CandidateMemory] = []
        for header, start, end in sections:
            lowered = header.lower()
            if not any(key in lowered for key in ("fixed", "security", "breaking")):
                continue

            severity = "high" if any(key in lowered for key in ("security", "breaking")) else "medium"
            for line_no in range(start, end):
                stripped = lines[line_no].strip()
                bullet = re.match(r"^[-*]\s+(.+)$", stripped)
                if not bullet:
                    continue
                fix = bullet.group(1).strip()
                out.append(
                    CandidateMemory(
                        memory_type="failure_pattern",
                        title=f"{header}: {fix}"[:140],
                        task_intent=f"Avoid known regression from changelog section '{header}'",
                        bad_suggestion=f"Repeat pre-fix behavior: {fix}",
                        failure_reason=f"Documented issue in CHANGELOG section '{header}'.",
                        prevention_rule=fix,
                        corrected_approach=fix,
                        severity=severity,
                        source_path=relative_path,
                        line_start=line_no + 1,
                        line_end=line_no + 1,
                        source_type="harvest:changelog",
                        extractor=self.name,
                        signal_strength=0.75,
                    )
                )
        return out

    @staticmethod
    def _sections(lines: list[str]) -> list[tuple[str, int, int]]:
        headers: list[tuple[str, int]] = []
        for i, line in enumerate(lines):
            match = re.match(r"^\s{0,3}#{2,6}\s+(.+)$", line)
            if match:
                headers.append((match.group(1).strip(), i))

        sections: list[tuple[str, int, int]] = []
        for idx, (header, pos) in enumerate(headers):
            start = pos + 1
            end = headers[idx + 1][1] if idx + 1 < len(headers) else len(lines)
            sections.append((header, start, end))
        return sections
