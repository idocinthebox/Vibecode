from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from vibecode.models import AgentProfile, FailurePattern, ProjectRule, SuccessPattern
from vibecode.services.search_service import SearchResult, SearchService
from vibecode.services.token_service import TokenService


class InjectionService:
    def __init__(self, base_dir: Path, conn: sqlite3.Connection | None = None) -> None:
        self.base_dir = Path(base_dir)
        self.search_service = SearchService(self.base_dir, conn)
        self.token_service = TokenService()

    def inject(self, query: str, profile: AgentProfile) -> str:
        results = self.search_service.search(query)

        failures = [r for r in results if r.result_type == "failure"]
        rules = [r for r in results if r.result_type == "rule"]
        successes = [r for r in results if r.result_type == "success"]

        lines: list[str] = [
            "# VibeCode Agent Context",
            "",
            f"## Task Query",
            query,
            "",
        ]

        sections: list[tuple[str, str, int]] = []

        if profile.include_failure_patterns and failures:
            critical_high = [f for f in failures if f.severity in ("critical", "high")]
            if critical_high:
                content = self._format_failures(critical_high)
                sections.append(("Relevant Failure Warnings", content, 0))
            other = [f for f in failures if f.severity not in ("critical", "high")]
            if other:
                content = self._format_failures(other)
                sections.append(("Relevant Failure Warnings", content, 1))

        if profile.include_project_rules and rules:
            content = self._format_rules(rules)
            sections.append(("Relevant Project Rules", content, 2))

        if profile.include_success_patterns and successes:
            content = self._format_successes(successes)
            sections.append(("Relevant Success Patterns", content, 3))

        budget = profile.max_context_tokens
        current_tokens = self.token_service.estimate_tokens("\n".join(lines))
        included: list[tuple[str, str]] = []

        sections.sort(key=lambda s: s[2])
        for name, content, _ in sections:
            section_tokens = self.token_service.estimate_tokens(content)
            if current_tokens + section_tokens <= budget:
                included.append((name, content))
                current_tokens += section_tokens
            elif name in ("Relevant Failure Warnings", "Relevant Project Rules"):
                trimmed = self._trim_content(content, budget - current_tokens)
                if trimmed:
                    included.append((name, trimmed))
                    current_tokens += self.token_service.estimate_tokens(trimmed)

        for name, content in included:
            lines.append(f"## {name}")
            lines.append("")
            lines.append(content)
            lines.append("")

        lines.append("## Token Budget")
        lines.append(f"- Profile limit: {profile.max_context_tokens} tokens")
        lines.append(f"- Estimated context used: {current_tokens} tokens")
        lines.append("")

        lines.append("## Instructions To Agent")
        lines.append(
            "Apply the above project rules and failure warnings before proposing code. "
            "Reuse the success patterns where applicable."
        )
        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _format_failures(results: list[SearchResult]) -> str:
        lines: list[str] = []
        for r in results:
            f = r.obj
            assert isinstance(f, FailurePattern)
            lines.append(f"- **[{f.severity.upper()}]** {f.prevention_rule}")
            lines.append(f"  - *Why:* {f.failure_reason}")
            if f.corrected_approach:
                lines.append(f"  - *Corrected approach:* {f.corrected_approach}")
        return "\n".join(lines)

    @staticmethod
    def _format_rules(results: list[SearchResult]) -> str:
        lines: list[str] = []
        for r in results:
            rule = r.obj
            assert isinstance(rule, ProjectRule)
            lines.append(f"- **[{rule.severity.upper()}]** {rule.rule_text}")
            lines.append(f"  - Type: {rule.rule_type}")
        return "\n".join(lines)

    @staticmethod
    def _format_successes(results: list[SearchResult]) -> str:
        lines: list[str] = []
        for r in results:
            s = r.obj
            assert isinstance(s, SuccessPattern)
            lines.append(f"- **{s.name}**")
            lines.append(f"  - *Intent:* {s.intent_description}")
            lines.append(f"  - *Summary:* {s.reasoning_summary}")
            if s.estimated_tokens_saved:
                lines.append(f"  - *Tokens saved:* ~{s.estimated_tokens_saved}")
        return "\n".join(lines)

    def _trim_content(self, content: str, max_tokens: int) -> str:
        lines = content.splitlines()
        trimmed: list[str] = []
        current = 0
        for line in lines:
            line_tokens = self.token_service.estimate_tokens(line)
            if current + line_tokens > max_tokens:
                break
            trimmed.append(line)
            current += line_tokens
        return "\n".join(trimmed)
