from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    REAL,
    TIMESTAMP,
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    projects: Mapped[List["Project"]] = relationship(back_populates="owner")
    success_patterns: Mapped[List["SuccessPattern"]] = relationship(
        back_populates="creator"
    )
    failure_patterns: Mapped[List["FailurePattern"]] = relationship(
        back_populates="creator"
    )
    agent_profiles: Mapped[List["AgentProfile"]] = relationship(
        back_populates="owner"
    )


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    owner_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    root_path: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    project_hash: Mapped[Optional[str]] = mapped_column(String(64))
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    owner: Mapped[Optional["User"]] = relationship(back_populates="projects")
    success_patterns: Mapped[List["SuccessPattern"]] = relationship(
        back_populates="project"
    )
    failure_patterns: Mapped[List["FailurePattern"]] = relationship(
        back_populates="project"
    )
    project_rules: Mapped[List["ProjectRule"]] = relationship(
        back_populates="project"
    )


class SuccessPattern(Base):
    __tablename__ = "success_patterns"

    id: Mapped[int] = mapped_column(primary_key=True)
    pattern_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL")
    )
    creator_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    intent_description: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[Optional[str]] = mapped_column(String(50))
    framework: Mapped[Optional[str]] = mapped_column(String(100))
    file_type: Mapped[Optional[str]] = mapped_column(String(100))
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    affected_files: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    original_prompt: Mapped[Optional[str]] = mapped_column(Text)
    reasoning_summary: Mapped[Optional[str]] = mapped_column(Text)
    reasoning_steps: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list
    )
    code_before: Mapped[Optional[str]] = mapped_column(Text)
    code_after: Mapped[Optional[str]] = mapped_column(Text)
    diff: Mapped[Optional[str]] = mapped_column(Text)
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    token_cost_original: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    token_cost_retrieval: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    estimated_tokens_saved: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    confidence_score: Mapped[float] = mapped_column(
        REAL, nullable=False, default=1.0
    )
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_rate: Mapped[float] = mapped_column(REAL, nullable=False, default=1.0)
    source_type: Mapped[Optional[str]] = mapped_column(String(50))
    source_ref: Mapped[Optional[str]] = mapped_column(Text)
    source_commit: Mapped[Optional[str]] = mapped_column(String(64))
    source_file_path: Mapped[Optional[str]] = mapped_column(Text)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64))
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
    last_used: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))

    project: Mapped[Optional["Project"]] = relationship(
        back_populates="success_patterns"
    )
    creator: Mapped[Optional["User"]] = relationship(
        back_populates="success_patterns"
    )
    embeddings: Mapped[List["PatternEmbedding"]] = relationship(
        back_populates="pattern"
    )


class FailurePattern(Base):
    __tablename__ = "failure_patterns"

    id: Mapped[int] = mapped_column(primary_key=True)
    failure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL")
    )
    creator_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    task_intent: Mapped[str] = mapped_column(Text, nullable=False)
    bad_suggestion: Mapped[str] = mapped_column(Text, nullable=False)
    failure_reason: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_approach: Mapped[Optional[str]] = mapped_column(Text)
    prevention_rule: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[Optional[str]] = mapped_column(String(50))
    framework: Mapped[Optional[str]] = mapped_column(String(100))
    affected_files: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    confidence_score: Mapped[float] = mapped_column(
        REAL, nullable=False, default=1.0
    )
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_type: Mapped[Optional[str]] = mapped_column(String(50))
    source_ref: Mapped[Optional[str]] = mapped_column(Text)
    source_commit: Mapped[Optional[str]] = mapped_column(String(64))
    source_file_path: Mapped[Optional[str]] = mapped_column(Text)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
    last_used: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))

    project: Mapped[Optional["Project"]] = relationship(
        back_populates="failure_patterns"
    )
    creator: Mapped[Optional["User"]] = relationship(
        back_populates="failure_patterns"
    )


class ProjectRule(Base):
    __tablename__ = "project_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    creator_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    rule_text: Mapped[str] = mapped_column(Text, nullable=False)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    source_success_pattern_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("success_patterns.id", ondelete="SET NULL")
    )
    source_failure_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("failure_patterns.id", ondelete="SET NULL")
    )
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    project: Mapped[Optional["Project"]] = relationship(
        back_populates="project_rules"
    )


class AgentProfile(Base):
    __tablename__ = "agent_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    owner_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    target_agent: Mapped[str] = mapped_column(String(100), nullable=False)
    max_context_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1500
    )
    include_success_patterns: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    include_failure_patterns: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    include_project_rules: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    include_recent_usage: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    output_format: Mapped[str] = mapped_column(
        String(50), nullable=False, default="markdown"
    )
    template: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    owner: Mapped[Optional["User"]] = relationship(back_populates="agent_profiles")

    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="idx_agent_profiles_owner_name"),
    )


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL")
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False)
    memory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    query_text: Mapped[Optional[str]] = mapped_column(Text)
    agent_profile: Mapped[Optional[str]] = mapped_column(String(100))
    tokens_saved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retrieval_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    was_useful: Mapped[Optional[bool]] = mapped_column(Boolean)
    was_modified: Mapped[Optional[bool]] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=utc_now
    )


class PatternEmbedding(Base):
    __tablename__ = "pattern_embeddings"

    id: Mapped[int] = mapped_column(primary_key=True)
    pattern_id: Mapped[int] = mapped_column(
        ForeignKey("success_patterns.id", ondelete="CASCADE"), nullable=False
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)
    embedding_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    embedding_dim: Mapped[int] = mapped_column(Integer, nullable=False, default=1536)
    embedding_input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    pattern: Mapped["SuccessPattern"] = relationship(back_populates="embeddings")

    __table_args__ = (
        UniqueConstraint(
            "pattern_id",
            "embedding_provider",
            "embedding_model",
            "embedding_version",
            name="uq_pattern_embedding",
        ),
    )
