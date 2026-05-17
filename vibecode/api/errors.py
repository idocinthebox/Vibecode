from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class VibeCodeAPIError(Exception):
    def __init__(self, code: str, message: str, fix: str = "") -> None:
        self.code = code
        self.message = message
        self.fix = fix


async def api_error_handler(request: Request, exc: VibeCodeAPIError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"error": exc.code, "message": exc.message, "fix": exc.fix},
    )
