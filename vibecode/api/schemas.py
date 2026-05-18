from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


def _validate_safe_absolute_path(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty")
    if "\x00" in cleaned:
        raise ValueError(f"{field_name} contains invalid null bytes")

    normalized = cleaned.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part not in ("", ".")]
    if any(part == ".." for part in parts):
        raise ValueError(f"{field_name} cannot contain path traversal segments")
    is_absolute = Path(cleaned).is_absolute() or PurePosixPath(cleaned).is_absolute()
    if not is_absolute:
        raise ValueError(f"{field_name} must be an absolute path")
    return cleaned


class SafePathModel(BaseModel):
    @model_validator(mode="after")
    def _validate_common_paths(self):
        for field_name in ("project_path", "file_path"):
            value = getattr(self, field_name, None)
            if value is None or value == "":
                continue
            _validate_safe_absolute_path(value, field_name)
        return self


class SearchMemoryRequest(SafePathModel):
    query: str
    project_path: str | None = None
    language: str | None = None
    framework: str | None = None
    include_success_patterns: bool = True
    include_failure_patterns: bool = True
    include_project_rules: bool = True
    max_results: int = 10


class SearchMemoryResult(BaseModel):
    memory_type: Literal["success_pattern", "failure_pattern", "project_rule"]
    memory_id: str
    title: str
    summary: str
    why_matched: str
    severity: str | None = None
    confidence_score: float | None = None
    source_type: str | None = None
    source_ref: str | None = None
    corrected_approach: str | None = None


class SearchMemoryResponse(BaseModel):
    query: str
    results: list[SearchMemoryResult]
    retrieval_time_ms: int


class InjectContextRequest(SafePathModel):
    query: str
    project_path: str | None = None
    agent_profile: str = "generic-agent"
    max_context_tokens: int | None = None
    include_failure_warnings: bool = True
    include_project_rules: bool = True
    include_success_patterns: bool = True


class InjectContextResponse(BaseModel):
    context_markdown: str
    estimated_context_tokens: int
    estimated_tokens_saved: int
    included_counts: dict[str, int]
    retrieval_time_ms: int


class CaptureSuccessRequest(SafePathModel):
    project_path: str
    name: str
    intent_description: str
    language: str | None = None
    framework: str | None = None
    affected_files: list[str] = Field(default_factory=list)
    original_prompt: str | None = None
    reasoning_summary: str | None = None
    code_before: str | None = None
    code_after: str | None = None
    diff: str | None = None
    explanation: str | None = None
    tags: list[str] = Field(default_factory=list)
    source_type: str = "manual"
    source_ref: str | None = None
    confidence: float | None = None
    occurrence_count: int | None = None
    last_seen_at: str | None = None
    agent_source: str | None = None
    review_state: Literal["pending", "confirmed", "discarded"] | None = None

    @field_validator("code_before", "code_after", "diff")
    @classmethod
    def _limit_code_fields(cls, value: str | None) -> str | None:
        if value is not None and len(value) > 10000:
            raise ValueError("code_* fields must be <= 10000 characters")
        return value

    @field_validator("tags")
    @classmethod
    def _limit_tags(cls, value: list[str]) -> list[str]:
        if len(value) > 50:
            raise ValueError("tags must contain <= 50 items")
        return value


class CaptureFailureRequest(SafePathModel):
    project_path: str
    task_intent: str
    bad_suggestion: str
    failure_reason: str
    corrected_approach: str | None = None
    prevention_rule: str
    language: str | None = None
    framework: str | None = None
    affected_files: list[str] = Field(default_factory=list)
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    tags: list[str] = Field(default_factory=list)
    source_type: str = "manual"
    source_ref: str | None = None
    confidence: float | None = None
    occurrence_count: int | None = None
    last_seen_at: str | None = None
    agent_source: str | None = None
    review_state: Literal["pending", "confirmed", "discarded"] | None = None

    @field_validator("task_intent")
    @classmethod
    def _limit_task_intent(cls, value: str) -> str:
        if len(value) > 500:
            raise ValueError("task_intent must be <= 500 characters")
        return value

    @field_validator("tags")
    @classmethod
    def _limit_tags(cls, value: list[str]) -> list[str]:
        if len(value) > 50:
            raise ValueError("tags must contain <= 50 items")
        return value


class AddProjectRuleRequest(SafePathModel):
    project_path: str
    rule_text: str
    rule_type: str
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    tags: list[str] = Field(default_factory=list)
    source_type: str = "manual"
    source_ref: str | None = None

    @field_validator("tags")
    @classmethod
    def _limit_tags(cls, value: list[str]) -> list[str]:
        if len(value) > 50:
            raise ValueError("tags must contain <= 50 items")
        return value


class CaptureResponse(BaseModel):
    pattern_id: str | None = None
    failure_id: str | None = None
    rule_id: str | None = None
    created: bool = True
    content_hash: str | None = None


class RuleResponse(BaseModel):
    rule_id: str
    created: bool = True


class TokenReportRequest(SafePathModel):
    project_path: str | None = None
    days: int = 30


class TokenReportResponse(BaseModel):
    success_patterns: int
    failure_patterns: int
    project_rules: int
    estimated_tokens_saved: int
    auto_captured_success: int
    auto_captured_failure: int
    prevention_hits: int
    estimated_tokens_saved_auto: int
    days: int


class HarvestScanRequest(SafePathModel):
    project_path: str
    include: list[str] = Field(default_factory=list)
    exclude: list[str] = Field(default_factory=list)
    max_files: int = 500
    auto_confirm_threshold: float = 0.8
    dry_run: bool = False


class HarvestCandidate(BaseModel):
    memory_type: Literal["project_rule", "failure_pattern", "success_pattern"]
    title: str
    source_type: str
    source_ref: str
    confidence: float
    review_state: Literal["pending", "confirmed", "discarded"]
    severity: str | None = None


class HarvestScanResponse(BaseModel):
    scanned_files: int
    candidates: int
    auto_confirmed: int
    queued_for_review: int
    duplicates_skipped: int
    report_id: str
    report_path: str
    candidate_items: list[HarvestCandidate] = Field(default_factory=list)
    extractor_counts: dict[str, int] = Field(default_factory=dict)


class HarvestReportResponse(HarvestScanResponse):
    generated_at: str | None = None


class EditRangeRequest(BaseModel):
    start_line: int = 0
    start_character: int = 0
    end_line: int = 0
    end_character: int = 0


class EditEventRequest(SafePathModel):
    event_id: str
    project_path: str
    file_path: str
    language: str = ""
    agent_source: str = "unknown"
    range: EditRangeRequest = Field(default_factory=EditRangeRequest)
    text_before: str = ""
    text_after: str = ""
    timestamp: float
    document_version: int = 0


class DiagnosticSignalRequest(SafePathModel):
    project_path: str
    file_path: str
    message: str = ""
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    is_new: bool = False
    is_resolved: bool = False
    timestamp: float


class TestSignalRequest(SafePathModel):
    project_path: str
    status_before: Literal["pass", "fail", "unknown"] = "unknown"
    status_after: Literal["pass", "fail", "unknown"] = "unknown"
    test_name: str = ""
    file_path: str = ""
    timestamp: float


class RevertSignalRequest(SafePathModel):
    project_path: str
    event_id: str
    reverted_to_text: str = ""
    timestamp: float


class TerminalSignalRequest(SafePathModel):
    project_path: str
    cwd: str
    command: str
    exit_code: int
    ended_at: float


class ObserveEditResponse(BaseModel):
    event_id: str


class PendingReviewItem(BaseModel):
    memory_type: Literal["success_pattern", "failure_pattern"]
    memory_id: str
    title: str
    summary: str
    confidence: float
    occurrence_count: int
    review_state: str
    agent_source: str | None = None
    last_seen_at: str | None = None


class ConfirmReviewRequest(BaseModel):
    memory_type: Literal["success_pattern", "failure_pattern"]
    edits: dict | None = None


class PreEditCheckRequest(SafePathModel):
    project_path: str
    file_path: str
    language: str
    proposed_text: str
    task_intent: str | None = None

    @field_validator("task_intent")
    @classmethod
    def _limit_task_intent(cls, value: str | None) -> str | None:
        if value is not None and len(value) > 500:
            raise ValueError("task_intent must be <= 500 characters")
        return value


class HealthResponse(BaseModel):
    status: str
    version: str
    storage_backend: str
    database_ok: bool
    allowed_projects_count: int


class ErrorResponse(BaseModel):
    error: str
    message: str
    fix: str
