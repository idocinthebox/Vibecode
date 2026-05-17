from __future__ import annotations

from fastapi import APIRouter

from vibecode.api.schemas import HealthResponse
from vibecode.core.memory_service import VibeCodeService

router = APIRouter()
service = VibeCodeService()


@router.get("/health", response_model=HealthResponse)
def health() -> dict:
    return service.health_check()
