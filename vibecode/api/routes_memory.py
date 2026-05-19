from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from vibecode.api.schemas import (
    AddProjectRuleRequest,
    CaptureFailureRequest,
    CaptureResponse,
    CaptureSuccessRequest,
    InjectContextRequest,
    InjectContextResponse,
    PreEditCheckRequest,
    RuleResponse,
    SearchMemoryRequest,
    SearchMemoryResponse,
    TokenReportBucketsResponse,
    TokenReportRequest,
    TokenReportResponse,
)
from vibecode.core.memory_service import VibeCodeService

router = APIRouter()


def get_service() -> VibeCodeService:
    """FastAPI dependency: instantiate service per-request to avoid SQLite threading issues."""
    return VibeCodeService()


@router.post("/memory/search", response_model=SearchMemoryResponse)
def search_memory(request: SearchMemoryRequest, service: VibeCodeService = Depends(get_service)) -> dict:
    return service.search_memory(
        query=request.query,
        project_path=request.project_path,
        language=request.language,
        framework=request.framework,
        include_success_patterns=request.include_success_patterns,
        include_failure_patterns=request.include_failure_patterns,
        include_project_rules=request.include_project_rules,
        max_results=request.max_results,
    )


@router.post("/memory/inject", response_model=InjectContextResponse)
def inject_context(request: InjectContextRequest, service: VibeCodeService = Depends(get_service)) -> dict:
    return service.inject_context(
        query=request.query,
        project_path=request.project_path,
        agent_profile=request.agent_profile,
        max_context_tokens=request.max_context_tokens,
        include_failure_warnings=request.include_failure_warnings,
        include_project_rules=request.include_project_rules,
        include_success_patterns=request.include_success_patterns,
    )


@router.post("/memory/capture-success", response_model=CaptureResponse)
def capture_success(request: CaptureSuccessRequest, service: VibeCodeService = Depends(get_service)) -> dict:
    result = service.capture_success(
        project_path=request.project_path,
        name=request.name,
        intent_description=request.intent_description,
        language=request.language,
        framework=request.framework,
        affected_files=request.affected_files,
        original_prompt=request.original_prompt,
        reasoning_summary=request.reasoning_summary,
        code_before=request.code_before,
        code_after=request.code_after,
        diff=request.diff,
        explanation=request.explanation,
        tags=request.tags,
        source_type=request.source_type,
        source_ref=request.source_ref,
        confidence=request.confidence,
        occurrence_count=request.occurrence_count,
        last_seen_at=request.last_seen_at,
        agent_source=request.agent_source,
        review_state=request.review_state,
    )
    if "error" in result:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail=result)
    return result


@router.post("/memory/capture-failure", response_model=CaptureResponse)
def capture_failure(request: CaptureFailureRequest, service: VibeCodeService = Depends(get_service)) -> dict:
    result = service.capture_failure(
        project_path=request.project_path,
        task_intent=request.task_intent,
        bad_suggestion=request.bad_suggestion,
        failure_reason=request.failure_reason,
        prevention_rule=request.prevention_rule,
        corrected_approach=request.corrected_approach,
        language=request.language,
        framework=request.framework,
        affected_files=request.affected_files,
        severity=request.severity,
        tags=request.tags,
        source_type=request.source_type,
        source_ref=request.source_ref,
        confidence=request.confidence,
        occurrence_count=request.occurrence_count,
        last_seen_at=request.last_seen_at,
        agent_source=request.agent_source,
        review_state=request.review_state,
    )
    if "error" in result:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail=result)
    return result


@router.post("/rules/add", response_model=RuleResponse)
def add_rule(request: AddProjectRuleRequest, service: VibeCodeService = Depends(get_service)) -> dict:
    result = service.add_project_rule(
        project_path=request.project_path,
        rule_text=request.rule_text,
        rule_type=request.rule_type,
        severity=request.severity,
        tags=request.tags,
        source_type=request.source_type,
        source_ref=request.source_ref,
    )
    if "error" in result:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail=result)
    return result


@router.post("/reports/tokens", response_model=TokenReportResponse)
def token_report(request: TokenReportRequest, service: VibeCodeService = Depends(get_service)) -> dict:
    return service.get_token_report(
        project_path=request.project_path,
        days=request.days,
    )


@router.post("/reports/tokens/buckets", response_model=TokenReportBucketsResponse)
def token_report_buckets(request: TokenReportRequest, service: VibeCodeService = Depends(get_service)) -> dict:
    return service.get_token_report_buckets(
        project_path=request.project_path,
        days=request.days,
    )


@router.post("/memory/pre-edit-check")
def pre_edit_check(request: PreEditCheckRequest, service: VibeCodeService = Depends(get_service)) -> dict:
    result = service.pre_edit_check(
        project_path=request.project_path,
        file_path=request.file_path,
        language=request.language,
        proposed_text=request.proposed_text,
        task_intent=request.task_intent,
    )
    if "error" in result:
        from fastapi import HTTPException

        raise HTTPException(status_code=429, detail=result)
    return result


@router.get("/memory/recent")
def recent_memory(
    memory_type: str = Query(..., alias="type"),
    limit: int = Query(25, ge=1, le=100),
    service: VibeCodeService = Depends(get_service),
) -> dict:
    return service.get_recent_memory(memory_type=memory_type, limit=limit)
