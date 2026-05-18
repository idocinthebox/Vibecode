from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from vibecode.api.schemas import (
    DiagnosticSignalRequest,
    EditEventRequest,
    ObserveEditResponse,
    RevertSignalRequest,
    TerminalSignalRequest,
    TestSignalRequest,
)
from vibecode.core.memory_service import VibeCodeService

router = APIRouter()


def get_service() -> VibeCodeService:
    """FastAPI dependency: instantiate service per-request to avoid SQLite threading issues."""
    return VibeCodeService()


@router.post("/observe/edit", response_model=ObserveEditResponse)
def observe_edit(request: EditEventRequest, service: VibeCodeService = Depends(get_service)) -> dict:
    result = service.observe_edit(request.model_dump())
    if "error" in result:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail=result)
    return result


@router.post("/observe/diagnostic", status_code=204)
def observe_diagnostic(request: DiagnosticSignalRequest, service: VibeCodeService = Depends(get_service)) -> Response:
    service.observe_diagnostic(request.model_dump())
    return Response(status_code=204)


@router.post("/observe/test", status_code=204)
def observe_test(request: TestSignalRequest, service: VibeCodeService = Depends(get_service)) -> Response:
    service.observe_test(request.model_dump())
    return Response(status_code=204)


@router.post("/observe/revert", status_code=204)
def observe_revert(request: RevertSignalRequest, service: VibeCodeService = Depends(get_service)) -> Response:
    service.observe_revert(request.model_dump())
    return Response(status_code=204)


@router.post("/observe/terminal", status_code=204)
def observe_terminal(request: TerminalSignalRequest, service: VibeCodeService = Depends(get_service)) -> Response:
    service.observe_terminal(request.model_dump())
    return Response(status_code=204)
