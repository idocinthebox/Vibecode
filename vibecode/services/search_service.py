from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from vibecode.models import FailurePattern, ProjectRule, SuccessPattern
from vibecode.repositories.failure_repository import FailureRepository
from vibecode.repositories.pattern_repository import PatternRepository
from vibecode.repositories.rule_repository import RuleRepository
from vibecode.storage.json_store import JsonStore


class SearchResult:
    def __init__(
        self,
        result_type: str,
        obj: SuccessPattern | FailurePattern | ProjectRule,
        matched_terms: list[str],
    ) -> None:
        self.result_type = result_type
        self.obj = obj
        self.matched_terms = matched_terms

    @property
    def memory_type(self) -> str:
        return self.result_type

    @property
    def memory_id(self) -> str:
        if isinstance(self.obj, SuccessPattern):
            return self.obj.pattern_id
        if isinstance(self.obj, FailurePattern):
            return self.obj.failure_id
        return self.obj.rule_id

    @property
    def title(self) -> str:
        if isinstance(self.obj, SuccessPattern):
            return self.obj.name
        if isinstance(self.obj, FailurePattern):
            return self.obj.task_intent
        return self.obj.rule_text

    @property
    def summary(self) -> str:
        if isinstance(self.obj, SuccessPattern):
            return self.obj.reasoning_summary
        if isinstance(self.obj, FailurePattern):
            return self.obj.prevention_rule
        return self.obj.rule_type

    @property
    def why_matched(self) -> str:
        return ", ".join(self.matched_terms)

    @property
    def confidence_score(self) -> float:
        if hasattr(self.obj, "confidence"):
            return float(getattr(self.obj, "confidence", 1.0))
        return float(getattr(self.obj, "confidence_score", 1.0))

    @property
    def tokens_estimate(self) -> int:
        if isinstance(self.obj, SuccessPattern):
            return self.obj.estimated_tokens_saved
        return 0

    @property
    def severity(self) -> str:
        if isinstance(self.obj, FailurePattern):
            return self.obj.severity
        if isinstance(self.obj, ProjectRule):
            return self.obj.severity
        return "low"

    @property
    def sort_key(self) -> tuple[int, int, float]:
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        rank = severity_order.get(self.severity, 3)
        type_order = {"failure": 0, "rule": 1, "success": 2}
        type_rank = type_order.get(self.result_type, 3)
        conf = -self.confidence_score
        return (rank, type_rank, conf)


class SearchService:
    def __init__(self, base_dir: Path, conn: sqlite3.Connection | None = None) -> None:
        self.base_dir = Path(base_dir)
        self.conn = conn
        if conn:
            self.pattern_repo = PatternRepository(conn)
            self.failure_repo = FailureRepository(conn)
            self.rule_repo = RuleRepository(conn)
        else:
            self.pattern_repo = None
            self.failure_repo = None
            self.rule_repo = None
        self.success_store = JsonStore(self.base_dir / "success_patterns")
        self.failure_store = JsonStore(self.base_dir / "failure_patterns")
        self.rule_store = JsonStore(self.base_dir / "project_rules")

    def search(self, query: str) -> list[SearchResult]:
        terms = [t.lower() for t in query.split() if t.strip()]
        if not terms:
            return []

        results: list[SearchResult] = []

        if self.pattern_repo:
            for pattern in self.pattern_repo.list_active():
                matched = self._match_success(pattern, terms)
                if matched:
                    results.append(SearchResult("success", pattern, matched))
        else:
            for data in self.success_store.load_all():
                if not data.get("is_active", True):
                    continue
                pattern = SuccessPattern.from_json(data)
                matched = self._match_success(pattern, terms)
                if matched:
                    results.append(SearchResult("success", pattern, matched))

        if self.failure_repo:
            for pattern in self.failure_repo.list_active():
                matched = self._match_failure(pattern, terms)
                if matched:
                    results.append(SearchResult("failure", pattern, matched))
        else:
            for data in self.failure_store.load_all():
                if not data.get("is_active", True):
                    continue
                pattern = FailurePattern.from_json(data)
                matched = self._match_failure(pattern, terms)
                if matched:
                    results.append(SearchResult("failure", pattern, matched))

        if self.rule_repo:
            for rule in self.rule_repo.list_active():
                matched = self._match_rule(rule, terms)
                if matched:
                    results.append(SearchResult("rule", rule, matched))
        else:
            for data in self.rule_store.load_all():
                if not data.get("is_active", True):
                    continue
                rule = ProjectRule.from_json(data)
                matched = self._match_rule(rule, terms)
                if matched:
                    results.append(SearchResult("rule", rule, matched))

        results.sort(key=lambda r: r.sort_key)
        return results

    def _match_terms(self, text: str, terms: list[str]) -> list[str]:
        if not text:
            return []
        text_lower = text.lower()
        return [t for t in terms if t in text_lower]

    def _match_success(self, pattern: SuccessPattern, terms: list[str]) -> list[str]:
        fields = [
            pattern.name,
            pattern.intent_description,
            pattern.language,
            pattern.framework,
            pattern.reasoning_summary,
            " ".join(pattern.tags),
            " ".join(pattern.affected_files),
        ]
        matched: set[str] = set()
        for field in fields:
            matched.update(self._match_terms(field, terms))
        return list(matched)

    def _match_failure(self, pattern: FailurePattern, terms: list[str]) -> list[str]:
        fields = [
            pattern.task_intent,
            pattern.bad_suggestion,
            pattern.failure_reason,
            pattern.prevention_rule,
            pattern.language,
            pattern.framework,
            " ".join(pattern.tags),
            " ".join(pattern.affected_files),
        ]
        matched: set[str] = set()
        for field in fields:
            matched.update(self._match_terms(field, terms))
        return list(matched)

    def _match_rule(self, rule: ProjectRule, terms: list[str]) -> list[str]:
        fields = [
            rule.rule_text,
            rule.rule_type,
            " ".join(rule.tags),
        ]
        matched: set[str] = set()
        for field in fields:
            matched.update(self._match_terms(field, terms))
        return list(matched)
