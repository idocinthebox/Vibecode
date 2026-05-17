from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sqlite3

from vibecode.models import AgentProfile, FailurePattern, ProjectRule, SuccessPattern
from vibecode.repositories.agent_profile_repository import AgentProfileRepository
from vibecode.repositories.failure_repository import FailureRepository
from vibecode.repositories.pattern_repository import PatternRepository
from vibecode.repositories.rule_repository import RuleRepository
from vibecode.services.hash_service import HashService
from vibecode.services.token_service import TokenService
from vibecode.storage.json_store import JsonStore


class CaptureService:
    def __init__(self, base_dir: Path, conn: sqlite3.Connection | None = None) -> None:
        self.base_dir = Path(base_dir)
        self.conn = conn
        if conn:
            self.pattern_repo = PatternRepository(conn)
            self.failure_repo = FailureRepository(conn)
            self.rule_repo = RuleRepository(conn)
            self.profile_repo = AgentProfileRepository(conn)
        else:
            self.pattern_repo = None
            self.failure_repo = None
            self.rule_repo = None
            self.profile_repo = None
        self.success_store = JsonStore(self.base_dir / "success_patterns")
        self.failure_store = JsonStore(self.base_dir / "failure_patterns")
        self.rule_store = JsonStore(self.base_dir / "project_rules")
        self.profile_store = JsonStore(self.base_dir / "agent_profiles")

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def capture_success(
        self, data: dict[str, Any]
    ) -> tuple[SuccessPattern, bool]:
        pattern_id = str(uuid.uuid4())
        data["pattern_id"] = pattern_id
        data.setdefault("created_at", self._now())
        data["updated_at"] = self._now()

        pattern = SuccessPattern(**data)
        pattern.content_hash = HashService.hash_success_pattern(pattern)

        # Deduplication via SQLite if available
        if self.pattern_repo:
            existing = self.pattern_repo.get_by_content_hash(pattern.content_hash)
            if existing:
                return existing, False
        else:
            existing = self._find_by_hash(
                self.success_store, "content_hash", pattern.content_hash
            )
            if existing:
                return SuccessPattern.from_json(existing), False

        # Token estimation
        original = pattern.token_cost_original or TokenService.estimate_tokens(
            pattern.original_prompt + pattern.reasoning_summary
        )
        retrieval = pattern.token_cost_retrieval or TokenService.estimate_tokens(
            pattern.reasoning_summary
        )
        pattern.token_cost_original = original
        pattern.token_cost_retrieval = retrieval
        pattern.estimated_tokens_saved = TokenService.estimate_tokens_saved(
            original, retrieval
        )

        if self.pattern_repo:
            self.pattern_repo.create(pattern)
        else:
            self.success_store.save(pattern_id, pattern.to_json())
        return pattern, True

    def capture_failure(
        self, data: dict[str, Any]
    ) -> tuple[FailurePattern, bool]:
        failure_id = str(uuid.uuid4())
        data["failure_id"] = failure_id
        data.setdefault("created_at", self._now())
        data["updated_at"] = self._now()

        pattern = FailurePattern(**data)
        pattern.content_hash = HashService.hash_failure_pattern(pattern)

        if self.failure_repo:
            existing = self.failure_repo.get_by_content_hash(pattern.content_hash)
            if existing:
                return existing, False
        else:
            existing = self._find_by_hash(
                self.failure_store, "content_hash", pattern.content_hash
            )
            if existing:
                return FailurePattern.from_json(existing), False

        if self.failure_repo:
            self.failure_repo.create(pattern)
        else:
            self.failure_store.save(failure_id, pattern.to_json())
        return pattern, True

    def add_rule(self, data: dict[str, Any]) -> ProjectRule:
        rule_id = str(uuid.uuid4())
        data["rule_id"] = rule_id
        data.setdefault("created_at", self._now())
        data["updated_at"] = self._now()

        rule = ProjectRule(**data)
        if self.rule_repo:
            self.rule_repo.create(rule)
        else:
            self.rule_store.save(rule_id, rule.to_json())
        return rule

    def seed_profiles(self) -> None:
        profiles = [
            {
                "profile_id": str(uuid.uuid4()),
                "name": "opus-review",
                "target_agent": "Claude Opus",
                "max_context_tokens": 1800,
                "template_path": "templates/opus_review.md",
            },
            {
                "profile_id": str(uuid.uuid4()),
                "name": "codex-build",
                "target_agent": "OpenAI Codex",
                "max_context_tokens": 1500,
                "template_path": "templates/codex_build.md",
            },
            {
                "profile_id": str(uuid.uuid4()),
                "name": "cursor-context",
                "target_agent": "Cursor Agent",
                "max_context_tokens": 1200,
                "template_path": "templates/cursor_rules.md",
            },
            {
                "profile_id": str(uuid.uuid4()),
                "name": "copilot-agent",
                "target_agent": "GitHub Copilot",
                "max_context_tokens": 1000,
                "template_path": "templates/copilot_agent.md",
            },
            {
                "profile_id": str(uuid.uuid4()),
                "name": "generic-agent",
                "target_agent": "Generic AI Agent",
                "max_context_tokens": 1500,
                "template_path": "templates/generic_agent.md",
            },
            {
                "profile_id": str(uuid.uuid4()),
                "name": "kimi-build",
                "target_agent": "Kimi 2.6",
                "max_context_tokens": 200000,
                "template_path": "templates/kimi_build.md",
            },
        ]
        for p in profiles:
            p.setdefault("created_at", self._now())
            p["updated_at"] = self._now()
            profile = AgentProfile(**p)
            if self.profile_repo:
                existing = self.profile_repo.get_by_name(profile.name)
                if not existing:
                    self.profile_repo.create(profile)
            else:
                if not self._find_by_field(self.profile_store, "name", profile.name):
                    self.profile_store.save(profile.profile_id, profile.to_json())

    def get_profile_by_name(self, name: str) -> AgentProfile | None:
        if self.profile_repo:
            return self.profile_repo.get_by_name(name)
        data = self._find_by_field(self.profile_store, "name", name)
        if data:
            return AgentProfile.from_json(data)
        return None

    @staticmethod
    def _find_by_hash(store: JsonStore, field: str, value: str) -> dict[str, Any] | None:
        for item in store.load_all():
            if item.get(field) == value:
                return item
        return None

    @staticmethod
    def _find_by_field(store: JsonStore, field: str, value: str) -> dict[str, Any] | None:
        for item in store.load_all():
            if item.get(field) == value:
                return item
        return None
