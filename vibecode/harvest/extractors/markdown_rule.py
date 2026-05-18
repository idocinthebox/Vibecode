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

_FAILURE_HEADING_HINTS = (
    "bug",
    "pitfall",
    "gotcha",
    "anti-pattern",
    "common mistake",
)


class MarkdownRuleExtractor:
    name = "MarkdownRuleExtractor"

    @staticmethod
    def matches(relative_path: str) -> bool:
        return relative_path.lower().endswith(".md")

    def extract(self, path: Path, relative_path: str) -> list[CandidateMemory]:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        out: list[CandidateMemory] = []
        out.extend(self._extract_imperative_rules(lines, relative_path))
        out.extend(self._extract_failure_sections(lines, relative_path))
        return out

    def _extract_imperative_rules(self, lines: list[str], relative_path: str) -> list[CandidateMemory]:
        out: list[CandidateMemory] = []
        in_fence = False
        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            if not stripped or stripped.startswith("#"):
                continue

            candidate = re.sub(r"^[-*]\s+", "", stripped)
            candidate = re.sub(r"^\d+\.\s+", "", candidate)
            lower = candidate.lower()
            if not any(lower.startswith(prefix) for prefix in _IMPERATIVE_PREFIXES):
                continue

            out.append(
                CandidateMemory(
                    memory_type="project_rule",
                    title=candidate[:140],
                    rule_text=candidate,
                    rule_type=self._infer_rule_type(candidate),
                    severity=self._infer_severity(candidate),
                    source_path=relative_path,
                    line_start=i,
                    line_end=i,
                    source_type="harvest:markdown_rule",
                    extractor=self.name,
                    signal_strength=0.7,
                )
            )
        return out

    def _extract_failure_sections(self, lines: list[str], relative_path: str) -> list[CandidateMemory]:
        out: list[CandidateMemory] = []
        heading_indexes: list[tuple[int, str]] = []

        for i, line in enumerate(lines):
            m = re.match(r"^\s{0,3}#{1,6}\s+(.+)$", line)
            if not m:
                continue
            heading = m.group(1).strip()
            if any(h in heading.lower() for h in _FAILURE_HEADING_HINTS):
                heading_indexes.append((i, heading))

        for idx, heading in heading_indexes:
            end = len(lines)
            for j in range(idx + 1, len(lines)):
                if re.match(r"^\s{0,3}#{1,6}\s+", lines[j]):
                    end = j
                    break

            block = lines[idx + 1 : end]
            failure_reason = self._first_text_block(block)
            code = self._first_code_block(block)
            fix_text = self._find_fix_text(block)
            if not failure_reason:
                failure_reason = heading
            if not fix_text:
                fix_text = "Follow the documented fix in this section."

            signal_strength = 0.6
            if code:
                signal_strength += 0.15
            if fix_text and "documented fix" not in fix_text.lower():
                signal_strength += 0.15

            out.append(
                CandidateMemory(
                    memory_type="failure_pattern",
                    title=heading[:140],
                    task_intent=heading,
                    bad_suggestion=code or f"See section: {heading}",
                    failure_reason=failure_reason,
                    prevention_rule=fix_text,
                    corrected_approach=fix_text,
                    severity=self._infer_failure_severity(heading, failure_reason),
                    source_path=relative_path,
                    line_start=idx + 1,
                    line_end=end,
                    source_type="harvest:markdown_rule",
                    extractor=self.name,
                    signal_strength=min(1.0, signal_strength),
                )
            )

        return out

    @staticmethod
    def _first_text_block(block: list[str]) -> str:
        chunks: list[str] = []
        in_fence = False
        for line in block:
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            if not stripped:
                if chunks:
                    break
                continue
            chunks.append(stripped)
            if len(chunks) >= 3:
                break
        return " ".join(chunks).strip()

    @staticmethod
    def _first_code_block(block: list[str]) -> str:
        in_fence = False
        captured: list[str] = []
        for line in block:
            stripped = line.rstrip("\n")
            if stripped.strip().startswith("```"):
                if not in_fence:
                    in_fence = True
                    continue
                break
            if in_fence:
                captured.append(stripped)
        return "\n".join(captured).strip()

    @staticmethod
    def _find_fix_text(block: list[str]) -> str:
        for line in block:
            m = re.search(r"\b(Fix|Solution):\s*(.+)$", line, flags=re.IGNORECASE)
            if m:
                return m.group(2).strip()
        return ""

    @staticmethod
    def _infer_rule_type(text: str) -> str:
        lower = text.lower()
        if any(k in lower for k in ("test", "pytest", "unit")):
            return "testing"
        if any(k in lower for k in ("dependency", "package", "import")):
            return "dependency"
        if any(k in lower for k in ("build", "compile", "release")):
            return "build"
        if any(k in lower for k in ("security", "secret", "token")):
            return "security"
        if any(k in lower for k in ("ui", "layout", "frontend")):
            return "ui"
        if any(k in lower for k in ("performance", "optimize", "latency")):
            return "performance"
        return "architecture"

    @staticmethod
    def _infer_severity(text: str) -> str:
        lower = text.lower()
        if lower.startswith("never") or lower.startswith("must") or lower.startswith("do not"):
            return "high"
        if lower.startswith("prefer"):
            return "medium"
        return "medium"

    @staticmethod
    def _infer_failure_severity(heading: str, reason: str) -> str:
        combined = f"{heading} {reason}".lower()
        if any(k in combined for k in ("security", "breaking", "critical")):
            return "high"
        return "medium"
