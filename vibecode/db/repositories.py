from __future__ import annotations

import uuid
from typing import Any, Sequence

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from vibecode.db.models import (
    AgentProfile,
    FailurePattern,
    ProjectRule,
    SuccessPattern,
    UsageEvent,
    User,
)


class PostgresPatternRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, pattern: SuccessPattern) -> SuccessPattern:
        self.session.add(pattern)
        self.session.commit()
        self.session.refresh(pattern)
        return pattern

    def get_by_uuid(self, pattern_uuid: uuid.UUID | str) -> SuccessPattern | None:
        stmt = select(SuccessPattern).where(SuccessPattern.pattern_id == str(pattern_uuid))
        return self.session.execute(stmt).scalar_one_or_none()

    def list_active(self) -> Sequence[SuccessPattern]:
        stmt = select(SuccessPattern).where(
            SuccessPattern.is_active.is_(True),
            SuccessPattern.is_deleted.is_(False),
        )
        return self.session.execute(stmt).scalars().all()

    def search(self, query: str) -> Sequence[SuccessPattern]:
        like = f"%{query}%"
        stmt = select(SuccessPattern).where(
            SuccessPattern.is_active.is_(True),
            SuccessPattern.is_deleted.is_(False),
        ).where(
            (SuccessPattern.name.ilike(like))
            | (SuccessPattern.intent_description.ilike(like))
            | (SuccessPattern.reasoning_summary.ilike(like))
            | (SuccessPattern.language.ilike(like))
            | (SuccessPattern.framework.ilike(like))
            | (SuccessPattern.tags.any(query))
        )
        return self.session.execute(stmt).scalars().all()

    def update(self, pattern: SuccessPattern) -> SuccessPattern:
        self.session.commit()
        self.session.refresh(pattern)
        return pattern

    def soft_delete(self, pattern_uuid: uuid.UUID | str) -> None:
        pattern = self.get_by_uuid(pattern_uuid)
        if pattern:
            pattern.is_active = False
            pattern.is_deleted = True
            self.session.commit()

    def get_by_content_hash(self, content_hash: str) -> SuccessPattern | None:
        stmt = select(SuccessPattern).where(
            SuccessPattern.content_hash == content_hash,
            SuccessPattern.is_deleted.is_(False),
        )
        return self.session.execute(stmt).scalar_one_or_none()


class PostgresFailureRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, pattern: FailurePattern) -> FailurePattern:
        self.session.add(pattern)
        self.session.commit()
        self.session.refresh(pattern)
        return pattern

    def get_by_uuid(self, failure_uuid: uuid.UUID | str) -> FailurePattern | None:
        stmt = select(FailurePattern).where(FailurePattern.failure_id == str(failure_uuid))
        return self.session.execute(stmt).scalar_one_or_none()

    def list_active(self) -> Sequence[FailurePattern]:
        stmt = select(FailurePattern).where(
            FailurePattern.is_active.is_(True),
            FailurePattern.is_deleted.is_(False),
        )
        return self.session.execute(stmt).scalars().all()

    def search(self, query: str) -> Sequence[FailurePattern]:
        like = f"%{query}%"
        stmt = select(FailurePattern).where(
            FailurePattern.is_active.is_(True),
            FailurePattern.is_deleted.is_(False),
        ).where(
            (FailurePattern.task_intent.ilike(like))
            | (FailurePattern.bad_suggestion.ilike(like))
            | (FailurePattern.failure_reason.ilike(like))
            | (FailurePattern.prevention_rule.ilike(like))
            | (FailurePattern.language.ilike(like))
            | (FailurePattern.framework.ilike(like))
            | (FailurePattern.tags.any(query))
        )
        return self.session.execute(stmt).scalars().all()

    def update(self, pattern: FailurePattern) -> FailurePattern:
        self.session.commit()
        self.session.refresh(pattern)
        return pattern

    def soft_delete(self, failure_uuid: uuid.UUID | str) -> None:
        pattern = self.get_by_uuid(failure_uuid)
        if pattern:
            pattern.is_active = False
            pattern.is_deleted = True
            self.session.commit()

    def get_by_content_hash(self, content_hash: str) -> FailurePattern | None:
        stmt = select(FailurePattern).where(
            FailurePattern.content_hash == content_hash,
            FailurePattern.is_deleted.is_(False),
        )
        return self.session.execute(stmt).scalar_one_or_none()


class PostgresProjectRuleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, rule: ProjectRule) -> ProjectRule:
        self.session.add(rule)
        self.session.commit()
        self.session.refresh(rule)
        return rule

    def get_by_uuid(self, rule_uuid: uuid.UUID | str) -> ProjectRule | None:
        stmt = select(ProjectRule).where(ProjectRule.rule_id == str(rule_uuid))
        return self.session.execute(stmt).scalar_one_or_none()

    def list_active(self) -> Sequence[ProjectRule]:
        stmt = select(ProjectRule).where(ProjectRule.is_active.is_(True))
        return self.session.execute(stmt).scalars().all()

    def search(self, query: str) -> Sequence[ProjectRule]:
        like = f"%{query}%"
        stmt = select(ProjectRule).where(ProjectRule.is_active.is_(True)).where(
            (ProjectRule.rule_text.ilike(like))
            | (ProjectRule.rule_type.ilike(like))
            | (ProjectRule.tags.any(query))
        )
        return self.session.execute(stmt).scalars().all()

    def update(self, rule: ProjectRule) -> ProjectRule:
        self.session.commit()
        self.session.refresh(rule)
        return rule

    def soft_delete(self, rule_uuid: uuid.UUID | str) -> None:
        rule = self.get_by_uuid(rule_uuid)
        if rule:
            rule.is_active = False
            self.session.commit()


class PostgresAgentProfileRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, profile: AgentProfile) -> AgentProfile:
        self.session.add(profile)
        self.session.commit()
        self.session.refresh(profile)
        return profile

    def get_by_uuid(self, profile_uuid: uuid.UUID | str) -> AgentProfile | None:
        stmt = select(AgentProfile).where(AgentProfile.profile_id == str(profile_uuid))
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_name(self, name: str) -> AgentProfile | None:
        stmt = select(AgentProfile).where(
            AgentProfile.name == name,
            AgentProfile.is_active.is_(True),
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_active(self) -> Sequence[AgentProfile]:
        stmt = select(AgentProfile).where(AgentProfile.is_active.is_(True))
        return self.session.execute(stmt).scalars().all()

    def update(self, profile: AgentProfile) -> AgentProfile:
        self.session.commit()
        self.session.refresh(profile)
        return profile

    def soft_delete(self, profile_uuid: uuid.UUID | str) -> None:
        profile = self.get_by_uuid(profile_uuid)
        if profile:
            profile.is_active = False
            self.session.commit()


class PostgresUsageRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, event: UsageEvent) -> UsageEvent:
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def list_for_memory(self, memory_type: str, memory_id: uuid.UUID) -> Sequence[UsageEvent]:
        stmt = (
            select(UsageEvent)
            .where(UsageEvent.memory_type == memory_type)
            .where(UsageEvent.memory_id == str(memory_id))
            .order_by(UsageEvent.created_at.desc())
        )
        return self.session.execute(stmt).scalars().all()

    def total_tokens_saved(self) -> int:
        stmt = select(func.coalesce(func.sum(UsageEvent.tokens_saved), 0))
        return self.session.execute(stmt).scalar_one()


class PostgresSearchRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def full_text_search_success(self, query: str, limit: int = 20) -> Sequence[SuccessPattern]:
        stmt = (
            select(SuccessPattern)
            .where(SuccessPattern.is_active.is_(True), SuccessPattern.is_deleted.is_(False))
            .where(
                text(
                    "to_tsvector('english', coalesce(name, '') || ' ' || coalesce(intent_description, '') || ' ' || coalesce(reasoning_summary, '')) @@ plainto_tsquery('english', :q)"
                ).bindparams(q=query)
            )
            .order_by(
                text(
                    "ts_rank(to_tsvector('english', coalesce(name, '') || ' ' || coalesce(intent_description, '') || ' ' || coalesce(reasoning_summary, '')), plainto_tsquery('english', :q)) DESC"
                ).bindparams(q=query)
            )
            .limit(limit)
        )
        return self.session.execute(stmt).scalars().all()

    def full_text_search_failure(self, query: str, limit: int = 20) -> Sequence[FailurePattern]:
        stmt = (
            select(FailurePattern)
            .where(FailurePattern.is_active.is_(True), FailurePattern.is_deleted.is_(False))
            .where(
                text(
                    "to_tsvector('english', coalesce(task_intent, '') || ' ' || coalesce(bad_suggestion, '') || ' ' || coalesce(failure_reason, '') || ' ' || coalesce(prevention_rule, '')) @@ plainto_tsquery('english', :q)"
                ).bindparams(q=query)
            )
            .order_by(
                text(
                    "ts_rank(to_tsvector('english', coalesce(task_intent, '') || ' ' || coalesce(bad_suggestion, '') || ' ' || coalesce(failure_reason, '') || ' ' || coalesce(prevention_rule, '')), plainto_tsquery('english', :q)) DESC"
                ).bindparams(q=query)
            )
            .limit(limit)
        )
        return self.session.execute(stmt).scalars().all()
