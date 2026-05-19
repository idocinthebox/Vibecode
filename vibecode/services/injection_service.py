from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from typing import Any

from vibecode.config.settings import get_service_settings
from vibecode.integrations.pro_sync import ProSyncAdapter
from vibecode.models import AgentProfile, FailurePattern, ProjectRule, SuccessPattern
from vibecode.services.search_service import SearchResult, SearchService
from vibecode.services.token_service import TokenService


class InjectionService:
    def __init__(self, base_dir: Path, conn: sqlite3.Connection | None = None) -> None:
        self.base_dir = Path(base_dir)
        self.search_service = SearchService(self.base_dir, conn)
        self.token_service = TokenService()
        self._last_remote_error = ""

    def inject(self, query: str, profile: AgentProfile) -> str:
        local_results = self.search_service.search(query)
        remote_results = self._search_remote(query)
        results = self._merge_and_rerank(local_results, remote_results) if remote_results else local_results

        failures = [r for r in results if r.result_type == "failure"]
        rules = [r for r in results if r.result_type == "rule"]
        successes = [r for r in results if r.result_type == "success"]

        lines: list[str] = [
            "# VibeCode Agent Context",
            "",
            "## Task Query",
            query,
            "",
        ]

        if not remote_results and self._last_remote_error:
            lines.append("## Pro Databank Unavailable")
            lines.append(f"- *Note:* {self._last_remote_error}")
            lines.append("")

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

    def _search_remote(self, query: str) -> list[SearchResult]:
        """Fetch optional Pro databank matches and map them into SearchResult objects."""
        self._last_remote_error = ""
        settings = get_service_settings()
        if not settings.pro_enabled:
            return []

        adapter = ProSyncAdapter(endpoint=settings.pro_endpoint, token=settings.pro_token)
        if not adapter.is_configured():
            return []

        payload = adapter.search(query=query, max_results=10)
        if "error" in payload:
            self._last_remote_error = str(payload["error"])
            return []

        terms = [t.lower() for t in query.split() if t.strip()]
        out: list[SearchResult] = []
        for item in payload.get("results", []):
            mapped = self._map_remote_item(item, terms)
            if mapped is not None:
                out.append(mapped)
        return out

    @staticmethod
    def _map_remote_item(item: dict[str, Any], terms: list[str]) -> SearchResult | None:
        memory_type = item.get("memory_type", "")
        rid = item.get("submission_id") or str(uuid.uuid4())
        title = item.get("title", "")
        summary = item.get("summary", "")
        confidence = float(item.get("usefulness", item.get("confidence_score", 0.6)))

        if memory_type == "failure_pattern":
            obj = FailurePattern(
                failure_id=rid,
                task_intent=title or "Remote failure pattern",
                bad_suggestion="",
                failure_reason=summary or "Remote failure pattern",
                prevention_rule=summary or "Review the related Pro pattern.",
                corrected_approach="",
                language=item.get("language", ""),
                framework=item.get("framework", ""),
                severity="medium",
                confidence_score=confidence,
                source_type="pro:global",
                source_ref=rid,
            )
            return SearchResult("failure", obj, terms)

        if memory_type == "success_pattern":
            obj = SuccessPattern(
                pattern_id=rid,
                name=title or "Remote success pattern",
                intent_description=summary or title or "Remote success pattern",
                language=item.get("language", ""),
                framework=item.get("framework", ""),
                reasoning_summary=summary or title or "Remote success pattern",
                confidence_score=confidence,
                confidence=confidence,
                source_type="pro:global",
                source_ref=rid,
            )
            return SearchResult("success", obj, terms)

        if memory_type == "project_rule":
            obj = ProjectRule(
                rule_id=rid,
                rule_text=title or summary or "Remote project rule",
                rule_type="failure_prevention",
                severity="medium",
                source_type="pro:global",
                source_ref=rid,
            )
            return SearchResult("rule", obj, terms)

        return None

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

    @staticmethod
    def _merge_and_rerank(
        local: list[SearchResult],
        remote: list[SearchResult],
        local_first_boost: float = 0.25,
    ) -> list[SearchResult]:
        """Merge local and remote search results with a local-first boost.

        Local results receive a +*local_first_boost* additive boost to their
        confidence score before sorting so that locally-validated patterns are
        preferred over remote (team/global) patterns of equal quality.

        Args:
            local: Results from the local SQLite store.
            remote: Results from the Pro databank.
            local_first_boost: Additive boost applied to local confidence scores.

        Returns:
            Merged list sorted by boosted score descending, deduplicated by title.
        """
        seen_keys: set[tuple[str, str, str]] = set()
        merged: list[tuple[float, SearchResult]] = []

        for r in local:
            score = (r.confidence_score or 0.0) + local_first_boost
            key = (r.result_type, r.title.strip().lower(), str(getattr(r.obj, "language", "") or "").lower())
            if key not in seen_keys:
                merged.append((score, r))
                seen_keys.add(key)

        for r in remote:
            score = r.confidence_score or 0.0
            key = (r.result_type, r.title.strip().lower(), str(getattr(r.obj, "language", "") or "").lower())
            if key not in seen_keys:
                merged.append((score, r))
                seen_keys.add(key)

        merged.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in merged]
