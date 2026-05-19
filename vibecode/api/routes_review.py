from __future__ import annotations

from fastapi import APIRouter, Depends

from vibecode.api.schemas import ConfirmReviewRequest, PendingReviewItem
from vibecode.core.memory_service import VibeCodeService

router = APIRouter()


def get_service() -> VibeCodeService:
    """FastAPI dependency: instantiate service per-request to avoid SQLite threading issues."""
    return VibeCodeService()


@router.get("/review/pending", response_model=list[PendingReviewItem])
def get_pending_review(service: VibeCodeService = Depends(get_service)) -> list[dict]:
    return service.get_pending_review()


@router.post("/review/{memory_id}/confirm")
def confirm_review(
    memory_id: str, request: ConfirmReviewRequest, service: VibeCodeService = Depends(get_service)
) -> dict:
    return service.confirm_review(
        memory_type=request.memory_type,
        memory_id=memory_id,
        edits=request.edits,
    )


@router.post("/review/{memory_id}/discard")
def discard_review(
    memory_id: str, request: ConfirmReviewRequest, service: VibeCodeService = Depends(get_service)
) -> dict:
    return service.discard_review(memory_type=request.memory_type, memory_id=memory_id)
