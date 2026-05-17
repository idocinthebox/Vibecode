from __future__ import annotations

from sqlalchemy.orm import Session

from vibecode.db.models import FailurePattern, ProjectRule, SuccessPattern
from vibecode.db.repositories import (
    PostgresAgentProfileRepository,
    PostgresFailureRepository,
    PostgresPatternRepository,
    PostgresProjectRuleRepository,
    PostgresSearchRepository,
)
from vibecode.services.search_service import SearchResult


class PostgresSearchService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.pattern_repo = PostgresPatternRepository(session)
        self.failure_repo = PostgresFailureRepository(session)
        self.rule_repo = PostgresProjectRuleRepository(session)
        self.search_repo = PostgresSearchRepository(session)
        self.profile_repo = PostgresAgentProfileRepository(session)

    def search(self, query: str) -> list[SearchResult]:
        terms = [t.lower() for t in query.split() if t.strip()]
        if not terms:
            return []

        results: list[SearchResult] = []

        # Try full-text first, fallback to ILIKE
        successes = self.search_repo.full_text_search_success(query)
        if not successes:
            successes = self.pattern_repo.search(query)

        failures = self.search_repo.full_text_search_failure(query)
        if not failures:
            failures = self.failure_repo.search(query)

        rules = self.rule_repo.search(query)

        for pattern in successes:
            matched = self._match_success_terms(pattern, terms)
            if matched:
                results.append(SearchResult("success", pattern, matched))

        for pattern in failures:
            matched = self._match_failure_terms(pattern, terms)
            if matched:
                results.append(SearchResult("failure", pattern, matched))

        for rule in rules:
            matched = self._match_rule_terms(rule, terms)
            if matched:
                results.append(SearchResult("rule", rule, matched))

        results.sort(key=lambda r: r.sort_key)
        return results

    def _match_terms(self, text: str, terms: list[str]) -> list[str]:
        if not text:
            return []
        text_lower = text.lower()
        return [t for t in terms if t in text_lower]

    def _match_success_terms(self, pattern: SuccessPattern, terms: list[str]) -> list[str]:
        fields = [
            pattern.name,
            pattern.intent_description,
            pattern.language or "",
            pattern.framework or "",
            pattern.reasoning_summary or "",
            " ".join(pattern.tags),
            " ".join(pattern.affected_files),
        ]
        matched: set[str] = set()
        for field in fields:
            matched.update(self._match_terms(field, terms))
        return list(matched)

    def _match_failure_terms(self, pattern: FailurePattern, terms: list[str]) -> list[str]:
        fields = [
            pattern.task_intent,
            pattern.bad_suggestion,
            pattern.failure_reason,
            pattern.prevention_rule,
            pattern.language or "",
            pattern.framework or "",
            " ".join(pattern.tags),
            " ".join(pattern.affected_files),
        ]
        matched: set[str] = set()
        for field in fields:
            matched.update(self._match_terms(field, terms))
        return list(matched)

    def _match_rule_terms(self, rule: ProjectRule, terms: list[str]) -> list[str]:
        fields = [
            rule.rule_text,
            rule.rule_type,
            " ".join(rule.tags),
        ]
        matched: set[str] = set()
        for field in fields:
            matched.update(self._match_terms(field, terms))
        return list(matched)
