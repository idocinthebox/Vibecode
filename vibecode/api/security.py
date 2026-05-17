from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class LocalhostOnlyMiddleware:
    def __init__(self, app, allow_all: bool = False) -> None:
        self.app = app
        self.allow_all = allow_all

    async def __call__(self, scope, receive, send):
        if not self.allow_all and scope.get("type") == "http":
            from starlette.requests import Request
            request = Request(scope, receive)
            client = request.client
            if client is not None:
                host = client.host or ""
                if host not in ("127.0.0.1", "::1", "localhost", "testclient", "testserver"):
                    from starlette.responses import JSONResponse
                    response = JSONResponse(
                        status_code=403,
                        content={
                            "error": "FORBIDDEN",
                            "message": "Requests must come from localhost.",
                            "fix": "Ensure the service is accessed from 127.0.0.1.",
                        },
                    )
                    await response(scope, receive, send)
                    return
        await self.app(scope, receive, send)
