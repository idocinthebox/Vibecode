from __future__ import annotations

import json
import os
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from vibecode.db.sqlite_connection import get_connection
from vibecode.db.sqlite_schema import create_schema
from vibecode.models import AgentProfile, FailurePattern, ProjectRule, SuccessPattern
from vibecode.repositories.agent_profile_repository import AgentProfileRepository
from vibecode.repositories.failure_repository import FailureRepository
from vibecode.repositories.pattern_repository import PatternRepository
from vibecode.repositories.rule_repository import RuleRepository


class MigrationService:
    def __init__(self, base_dir: Path, conn: sqlite3.Connection | None = None) -> None:
        self.base_dir = Path(base_dir)
        self.conn = conn or get_connection(base_dir)

    def migrate(self) -> dict[str, int]:
        create_schema(self.conn)
        pattern_repo = PatternRepository(self.conn)
        failure_repo = FailureRepository(self.conn)
        rule_repo = RuleRepository(self.conn)
        profile_repo = AgentProfileRepository(self.conn)

        counts = {
            "success_patterns": 0,
            "failure_patterns": 0,
            "project_rules": 0,
            "agent_profiles": 0,
            "duplicates_skipped": 0,
            "errors": 0,
        }

        # Success patterns
        success_dir = self.base_dir / "success_patterns"
        if success_dir.exists():
            for filename in os.listdir(success_dir):
                if not filename.endswith(".json"):
                    continue
                try:
                    with open(success_dir / filename, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    pattern = SuccessPattern(**data)
                    if not pattern.content_hash:
                        from vibecode.services.hash_service import HashService
                        pattern.content_hash = HashService.hash_success_pattern(pattern)
                    existing = pattern_repo.get_by_content_hash(pattern.content_hash)
                    if existing:
                        counts["duplicates_skipped"] += 1
                        continue
                    pattern_repo.create(pattern)
                    counts["success_patterns"] += 1
                except Exception:
                    counts["errors"] += 1

        # Failure patterns
        failure_dir = self.base_dir / "failure_patterns"
        if failure_dir.exists():
            for filename in os.listdir(failure_dir):
                if not filename.endswith(".json"):
                    continue
                try:
                    with open(failure_dir / filename, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    pattern = FailurePattern(**data)
                    if not pattern.content_hash:
                        from vibecode.services.hash_service import HashService
                        pattern.content_hash = HashService.hash_failure_pattern(pattern)
                    existing = failure_repo.get_by_content_hash(pattern.content_hash)
                    if existing:
                        counts["duplicates_skipped"] += 1
                        continue
                    failure_repo.create(pattern)
                    counts["failure_patterns"] += 1
                except Exception:
                    counts["errors"] += 1

        # Project rules
        rules_dir = self.base_dir / "project_rules"
        if rules_dir.exists():
            for filename in os.listdir(rules_dir):
                if not filename.endswith(".json"):
                    continue
                try:
                    with open(rules_dir / filename, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    rule = ProjectRule(**data)
                    existing = rule_repo.get_by_id(rule.rule_id)
                    if existing:
                        counts["duplicates_skipped"] += 1
                        continue
                    rule_repo.create(rule)
                    counts["project_rules"] += 1
                except Exception:
                    counts["errors"] += 1

        # Agent profiles
        profiles_dir = self.base_dir / "agent_profiles"
        if profiles_dir.exists():
            for filename in os.listdir(profiles_dir):
                if not filename.endswith(".json"):
                    continue
                try:
                    with open(profiles_dir / filename, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    profile = AgentProfile(**data)
                    existing = profile_repo.get_by_id(profile.profile_id)
                    if existing:
                        counts["duplicates_skipped"] += 1
                        continue
                    profile_repo.create(profile)
                    counts["agent_profiles"] += 1
                except Exception:
                    counts["errors"] += 1

        return counts
