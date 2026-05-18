from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SuccessPattern(BaseModel):
    pattern_id: str
    name: str
    intent_description: str
    language: str = ""
    framework: str = ""
    file_type: str = ""
    tags: list[str] = Field(default_factory=list)
    affected_files: list[str] = Field(default_factory=list)

    original_prompt: str = ""
    reasoning_summary: str
    reasoning_steps: list[str] = Field(default_factory=list)

    code_before: str = ""
    code_after: str = ""
    diff: str = ""
    explanation: str = ""

    token_cost_original: int = 0
    token_cost_retrieval: int = 0
    estimated_tokens_saved: int = 0

    confidence_score: float = 1.0
    usage_count: int = 0
    success_rate: float = 1.0
    confidence: float = 1.0
    occurrence_count: int = 1
    last_seen_at: str | None = None
    agent_source: str = ""
    review_state: str = "confirmed"

    source_type: str = "manual"
    source_ref: str = ""
    harvest_meta: dict[str, Any] = Field(default_factory=dict)
    shared_publication_id: str | None = None
    source_commit: str = ""
    source_file_path: str = ""
    content_hash: str = ""

    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)
    last_used: str | None = None
    is_active: bool = True

    @field_validator("tags", "affected_files", "reasoning_steps", mode="before")
    @classmethod
    def _coerce_list(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v or []

    @field_validator("review_state")
    @classmethod
    def _valid_review_state(cls, v: str) -> str:
        allowed = {"pending", "confirmed", "discarded"}
        if v not in allowed:
            raise ValueError(f"review_state must be one of {allowed}")
        return v

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> SuccessPattern:
        return cls(**data)


class FailurePattern(BaseModel):
    failure_id: str
    task_intent: str
    bad_suggestion: str
    failure_reason: str
    corrected_approach: str = ""
    prevention_rule: str

    language: str = ""
    framework: str = ""
    affected_files: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    severity: str
    confidence_score: float = 1.0
    usage_count: int = 0
    confidence: float = 1.0
    occurrence_count: int = 1
    last_seen_at: str | None = None
    agent_source: str = ""
    review_state: str = "confirmed"

    source_type: str = "manual"
    source_ref: str = ""
    harvest_meta: dict[str, Any] = Field(default_factory=dict)
    shared_publication_id: str | None = None
    source_commit: str = ""
    source_file_path: str = ""
    content_hash: str = ""

    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)
    last_used: str | None = None
    is_active: bool = True

    @field_validator("severity")
    @classmethod
    def _valid_severity(cls, v: str) -> str:
        allowed = {"low", "medium", "high", "critical"}
        if v not in allowed:
            raise ValueError(f"severity must be one of {allowed}")
        return v

    @field_validator("review_state")
    @classmethod
    def _valid_review_state(cls, v: str) -> str:
        allowed = {"pending", "confirmed", "discarded"}
        if v not in allowed:
            raise ValueError(f"review_state must be one of {allowed}")
        return v

    @field_validator("tags", "affected_files", mode="before")
    @classmethod
    def _coerce_list(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v or []

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> FailurePattern:
        return cls(**data)


class ProjectRule(BaseModel):
    rule_id: str
    rule_text: str
    rule_type: str
    severity: str
    tags: list[str] = Field(default_factory=list)

    source_success_pattern_id: str = ""
    source_failure_id: str = ""
    source_type: str = "manual"
    source_ref: str = ""
    harvest_meta: dict[str, Any] = Field(default_factory=dict)
    review_state: str = "confirmed"
    shared_publication_id: str | None = None

    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)
    is_active: bool = True

    @field_validator("severity")
    @classmethod
    def _valid_severity(cls, v: str) -> str:
        allowed = {"low", "medium", "high", "critical"}
        if v not in allowed:
            raise ValueError(f"severity must be one of {allowed}")
        return v

    @field_validator("rule_type")
    @classmethod
    def _valid_rule_type(cls, v: str) -> str:
        allowed = {
            "architecture",
            "dependency",
            "ui",
            "testing",
            "build",
            "packaging",
            "agent_behavior",
            "failure_prevention",
            "performance",
            "security",
        }
        if v not in allowed:
            raise ValueError(f"rule_type must be one of {allowed}")
        return v

    @field_validator("review_state")
    @classmethod
    def _valid_review_state(cls, v: str) -> str:
        allowed = {"pending", "confirmed", "discarded"}
        if v not in allowed:
            raise ValueError(f"review_state must be one of {allowed}")
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def _coerce_list(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v or []

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> ProjectRule:
        return cls(**data)


class AgentProfile(BaseModel):
    profile_id: str
    name: str
    target_agent: str
    max_context_tokens: int
    include_success_patterns: bool = True
    include_failure_patterns: bool = True
    include_project_rules: bool = True
    include_recent_usage: bool = False
    output_format: str = "markdown"
    template_path: str = ""
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)
    is_active: bool = True

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> AgentProfile:
        return cls(**data)
