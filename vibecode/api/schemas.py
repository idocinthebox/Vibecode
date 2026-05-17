from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SearchMemoryRequest(BaseModel):
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


class InjectContextRequest(BaseModel):
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


class CaptureSuccessRequest(BaseModel):
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


class CaptureFailureRequest(BaseModel):
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


class AddProjectRuleRequest(BaseModel):
    project_path: str
    rule_text: str
    rule_type: str
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    tags: list[str] = Field(default_factory=list)
    source_type: str = "manual"
    source_ref: str | None = None


class CaptureResponse(BaseModel):
    pattern_id: str | None = None
    failure_id: str | None = None
    rule_id: str | None = None
    created: bool = True
    content_hash: str | None = None


class RuleResponse(BaseModel):
    rule_id: str
    created: bool = True


class TokenReportRequest(BaseModel):
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


class EditRangeRequest(BaseModel):
    start_line: int = 0
    start_character: int = 0
    end_line: int = 0
    end_character: int = 0


class EditEventRequest(BaseModel):
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


class DiagnosticSignalRequest(BaseModel):
    project_path: str
    file_path: str
    message: str = ""
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    is_new: bool = False
    is_resolved: bool = False
    timestamp: float


class TestSignalRequest(BaseModel):
    project_path: str
    status_before: Literal["pass", "fail", "unknown"] = "unknown"
    status_after: Literal["pass", "fail", "unknown"] = "unknown"
    test_name: str = ""
    file_path: str = ""
    timestamp: float


class RevertSignalRequest(BaseModel):
    project_path: str
    event_id: str
    reverted_to_text: str = ""
    timestamp: float


class TerminalSignalRequest(BaseModel):
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


class PreEditCheckRequest(BaseModel):
    project_path: str
    file_path: str
    language: str
    proposed_text: str
    task_intent: str | None = None


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
