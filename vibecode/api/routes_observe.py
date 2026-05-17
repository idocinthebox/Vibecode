from __future__ import annotations

from fastapi import APIRouter, Response

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
service = VibeCodeService()


@router.post("/observe/edit", response_model=ObserveEditResponse)
def observe_edit(request: EditEventRequest) -> dict:
    result = service.observe_edit(request.model_dump())
    if "error" in result:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail=result)
    return result


@router.post("/observe/diagnostic", status_code=204)
def observe_diagnostic(request: DiagnosticSignalRequest) -> Response:
    service.observe_diagnostic(request.model_dump())
    return Response(status_code=204)


@router.post("/observe/test", status_code=204)
def observe_test(request: TestSignalRequest) -> Response:
    service.observe_test(request.model_dump())
    return Response(status_code=204)


@router.post("/observe/revert", status_code=204)
def observe_revert(request: RevertSignalRequest) -> Response:
    service.observe_revert(request.model_dump())
    return Response(status_code=204)


@router.post("/observe/terminal", status_code=204)
def observe_terminal(request: TerminalSignalRequest) -> Response:
    service.observe_terminal(request.model_dump())
    return Response(status_code=204)
