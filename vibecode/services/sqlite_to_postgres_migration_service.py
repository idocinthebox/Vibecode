from __future__ import annotations

import sqlite3
from pathlib import Path

from sqlalchemy.orm import Session

from vibecode.db.models import (
    AgentProfile,
    FailurePattern,
    Project,
    ProjectRule,
    SuccessPattern,
    User,
)
from vibecode.db.repositories import (
    PostgresAgentProfileRepository,
    PostgresFailureRepository,
    PostgresPatternRepository,
    PostgresProjectRuleRepository,
)


class SqliteToPostgresMigrationService:
    def __init__(self, sqlite_path: Path, session: Session) -> None:
        self.sqlite_path = sqlite_path
        self.session = session
        self.pattern_repo = PostgresPatternRepository(session)
        self.failure_repo = PostgresFailureRepository(session)
        self.rule_repo = PostgresProjectRuleRepository(session)
        self.profile_repo = PostgresAgentProfileRepository(session)

    def migrate(self) -> dict[str, int]:
        conn = sqlite3.connect(str(self.sqlite_path))
        conn.row_factory = sqlite3.Row

        counts = {
            "users": 0,
            "projects": 0,
            "success_patterns": 0,
            "failure_patterns": 0,
            "project_rules": 0,
            "agent_profiles": 0,
            "usage_events": 0,
            "duplicates_skipped": 0,
            "errors": 0,
        }

        # Default user
        user = User(username="default", email="default@local")
        self.session.add(user)
        self.session.commit()
        counts["users"] = 1

        # Default project
        project = Project(name="default", owner_id=user.id)
        self.session.add(project)
        self.session.commit()
        counts["projects"] = 1

        # Success patterns
        try:
            rows = conn.execute("SELECT * FROM success_patterns").fetchall()
            for row in rows:
                try:
                    data = dict(row)
                    import json
                    tags = json.loads(data.get("tags_json", "[]"))
                    affected_files = json.loads(data.get("affected_files_json", "[]"))
                    reasoning_steps = json.loads(data.get("reasoning_steps_json", "[]"))

                    existing = self.pattern_repo.get_by_content_hash(data.get("content_hash", ""))
                    if existing:
                        counts["duplicates_skipped"] += 1
                        continue

                    pattern = SuccessPattern(
                        pattern_id=data["pattern_id"],
                        project_id=project.id,
                        creator_id=user.id,
                        name=data["name"],
                        intent_description=data["intent_description"],
                        language=data.get("language"),
                        framework=data.get("framework"),
                        file_type=data.get("file_type"),
                        tags=tags,
                        affected_files=affected_files,
                        original_prompt=data.get("original_prompt"),
                        reasoning_summary=data.get("reasoning_summary"),
                        reasoning_steps=reasoning_steps,
                        code_before=data.get("code_before"),
                        code_after=data.get("code_after"),
                        diff=data.get("diff"),
                        explanation=data.get("explanation"),
                        token_cost_original=data.get("token_cost_original", 0),
                        token_cost_retrieval=data.get("token_cost_retrieval", 0),
                        estimated_tokens_saved=data.get("estimated_tokens_saved", 0),
                        confidence_score=data.get("confidence_score", 1.0),
                        usage_count=data.get("usage_count", 0),
                        success_rate=data.get("success_rate", 1.0),
                        source_type=data.get("source_type"),
                        source_ref=data.get("source_ref"),
                        source_commit=data.get("source_commit"),
                        source_file_path=data.get("source_file_path"),
                        content_hash=data.get("content_hash"),
                        is_active=bool(data.get("is_active", 1)),
                        created_at=data["created_at"],
                        updated_at=data["updated_at"],
                        last_used=data.get("last_used"),
                    )
                    self.pattern_repo.create(pattern)
                    counts["success_patterns"] += 1
                except Exception:
                    counts["errors"] += 1
        except Exception:
            pass

        # Failure patterns
        try:
            rows = conn.execute("SELECT * FROM failure_patterns").fetchall()
            for row in rows:
                try:
                    data = dict(row)
                    import json
                    tags = json.loads(data.get("tags_json", "[]"))
                    affected_files = json.loads(data.get("affected_files_json", "[]"))

                    existing = self.failure_repo.get_by_content_hash(data.get("content_hash", ""))
                    if existing:
                        counts["duplicates_skipped"] += 1
                        continue

                    pattern = FailurePattern(
                        failure_id=data["failure_id"],
                        project_id=project.id,
                        creator_id=user.id,
                        task_intent=data["task_intent"],
                        bad_suggestion=data["bad_suggestion"],
                        failure_reason=data["failure_reason"],
                        corrected_approach=data.get("corrected_approach"),
                        prevention_rule=data["prevention_rule"],
                        language=data.get("language"),
                        framework=data.get("framework"),
                        affected_files=affected_files,
                        tags=tags,
                        severity=data.get("severity", "medium"),
                        confidence_score=data.get("confidence_score", 1.0),
                        usage_count=data.get("usage_count", 0),
                        source_type=data.get("source_type"),
                        source_ref=data.get("source_ref"),
                        source_commit=data.get("source_commit"),
                        source_file_path=data.get("source_file_path"),
                        content_hash=data.get("content_hash"),
                        is_active=bool(data.get("is_active", 1)),
                        created_at=data["created_at"],
                        updated_at=data["updated_at"],
                        last_used=data.get("last_used"),
                    )
                    self.failure_repo.create(pattern)
                    counts["failure_patterns"] += 1
                except Exception:
                    counts["errors"] += 1
        except Exception:
            pass

        # Project rules
        try:
            rows = conn.execute("SELECT * FROM project_rules").fetchall()
            for row in rows:
                try:
                    data = dict(row)
                    import json
                    tags = json.loads(data.get("tags_json", "[]"))

                    existing = self.rule_repo.get_by_uuid(data["rule_id"])
                    if existing:
                        counts["duplicates_skipped"] += 1
                        continue

                    rule = ProjectRule(
                        rule_id=data["rule_id"],
                        project_id=project.id,
                        creator_id=user.id,
                        rule_text=data["rule_text"],
                        rule_type=data["rule_type"],
                        severity=data.get("severity", "medium"),
                        source_success_pattern_id=None,
                        source_failure_id=None,
                        tags=tags,
                        is_active=bool(data.get("is_active", 1)),
                        created_at=data["created_at"],
                        updated_at=data["updated_at"],
                    )
                    self.rule_repo.create(rule)
                    counts["project_rules"] += 1
                except Exception:
                    counts["errors"] += 1
        except Exception:
            pass

        # Agent profiles
        try:
            rows = conn.execute("SELECT * FROM agent_profiles").fetchall()
            for row in rows:
                try:
                    data = dict(row)
                    existing = self.profile_repo.get_by_uuid(data["profile_id"])
                    if existing:
                        counts["duplicates_skipped"] += 1
                        continue

                    profile = AgentProfile(
                        profile_id=data["profile_id"],
                        owner_id=user.id,
                        name=data["name"],
                        target_agent=data["target_agent"],
                        max_context_tokens=data.get("max_context_tokens", 1500),
                        include_success_patterns=bool(data.get("include_success_patterns", 1)),
                        include_failure_patterns=bool(data.get("include_failure_patterns", 1)),
                        include_project_rules=bool(data.get("include_project_rules", 1)),
                        include_recent_usage=bool(data.get("include_recent_usage", 0)),
                        output_format=data.get("output_format", "markdown"),
                        template=data.get("template_path"),
                        is_active=True,
                        created_at=data["created_at"],
                        updated_at=data["updated_at"],
                    )
                    self.profile_repo.create(profile)
                    counts["agent_profiles"] += 1
                except Exception:
                    counts["errors"] += 1
        except Exception:
            pass

        conn.close()
        return counts
