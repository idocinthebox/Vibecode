from __future__ import annotations

from fastapi import APIRouter

from vibecode.api.schemas import ConfirmReviewRequest, PendingReviewItem
from vibecode.core.memory_service import VibeCodeService

router = APIRouter()
service = VibeCodeService()


@router.get("/review/pending", response_model=list[PendingReviewItem])
def get_pending_review() -> list[dict]:
    return service.get_pending_review()


@router.post("/review/{memory_id}/confirm")
def confirm_review(memory_id: str, request: ConfirmReviewRequest) -> dict:
    return service.confirm_review(
        memory_type=request.memory_type,
        memory_id=memory_id,
        edits=request.edits,
    )


@router.post("/review/{memory_id}/discard")
def discard_review(memory_id: str, request: ConfirmReviewRequest) -> dict:
    return service.discard_review(memory_type=request.memory_type, memory_id=memory_id)
