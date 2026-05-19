"""FastAPI routes for Pro databank integration on the local service.

POST /pro/share/{memory_type}/{memory_id}  — share a pattern to the Pro databank
POST /pro/retract                          — retract a submission
GET  /pro/status                           — Pro connection status
POST /pro/search                           — search the Pro databank
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from vibecode.core.memory_service import VibeCodeService

router = APIRouter()


def get_service() -> VibeCodeService:
    return VibeCodeService()


class ProShareRequest(BaseModel):
    project_path: str = ""


class ProRetractRequest(BaseModel):
    submission_id: str


class ProSearchRequest(BaseModel):
    query: str
    max_results: int = 10


@router.post("/pro/share/{memory_type}/{memory_id}")
def pro_share(
    memory_type: str,
    memory_id: str,
    request: ProShareRequest,
    service: VibeCodeService = Depends(get_service),
) -> dict:
    return service.pro_share(memory_type=memory_type, memory_id=memory_id)


@router.post("/pro/retract")
def pro_retract(
    request: ProRetractRequest,
    service: VibeCodeService = Depends(get_service),
) -> dict:
    return service.pro_retract(submission_id=request.submission_id)


@router.get("/pro/status")
def pro_status(service: VibeCodeService = Depends(get_service)) -> dict:
    return service.pro_status()


@router.post("/pro/search")
def pro_search(
    request: ProSearchRequest,
    service: VibeCodeService = Depends(get_service),
) -> dict:
    return service.pro_search(query=request.query, max_results=request.max_results)


@router.post("/memory/check-command")
def check_command(request: dict, service: VibeCodeService = Depends(get_service)) -> dict:
    """Phase 8: check a shell command against failure patterns before execution."""
    command = request.get("command", "")
    project_path = request.get("project_path")
    return service.check_command(command=command, project_path=project_path)


@router.post("/memory/recall-on-error")
def recall_on_error(request: dict, service: VibeCodeService = Depends(get_service)) -> dict:
    """Phase 8: search memory for patterns matching terminal error output."""
    error_output = request.get("error_output", "")
    project_path = request.get("project_path")
    command = request.get("command")
    return service.recall_on_error(error_output=error_output, project_path=project_path, command=command)
