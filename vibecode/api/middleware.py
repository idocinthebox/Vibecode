"""Rate-limit ASGI middleware for VibeCode local service.

Implements a per-(client-IP, route-prefix) sliding-window token bucket.
The default rate is ``rate_limit_default_per_min`` from ServiceSettings.
Routes under ``/memory/pre-edit-check`` use the tighter
``pre_edit_check_rate_limit_per_min`` limit.

Returns HTTP 429 with a JSON body when the limit is exceeded.
"""

from __future__ import annotations

import json
import time
from collections import defaultdict, deque
from collections.abc import Callable

ENDPOINT_LIMITS: dict[str, str] = {
    "/memory/pre-edit-check": "pre_edit_check_rate_limit_per_min",
}


class RateLimitMiddleware:
    """Sliding-window rate-limiter middleware (60-second window)."""

    def __init__(self, app, default_per_min: int = 120, pre_edit_check_per_min: int = 30) -> None:
        self.app = app
        self.default_per_min = default_per_min
        self.pre_edit_check_per_min = pre_edit_check_per_min
        # {(client_ip, route_key): deque[timestamp]}
        self._windows: dict[tuple[str, str], deque] = defaultdict(deque)

    def _get_client_ip(self, scope: dict) -> str:
        client = scope.get("client")
        if client:
            return client[0]
        return "unknown"

    def _get_limit(self, path: str) -> int:
        if path.startswith("/memory/pre-edit-check"):
            return self.pre_edit_check_per_min
        return self.default_per_min

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")
        client_ip = self._get_client_ip(scope)
        limit = self._get_limit(path)
        window_key = (client_ip, path)
        now = time.time()
        window = self._windows[window_key]

        # Evict entries older than 60 seconds
        while window and (now - window[0]) > 60.0:
            window.popleft()
        if not window:
            self._windows.pop(window_key, None)
            window = self._windows[window_key]

        if len(window) >= limit:
            body = json.dumps(
                {
                    "error": "RATE_LIMITED",
                    "message": "Too many requests. Reduce call frequency or wait one minute.",
                    "limit_per_min": limit,
                }
            ).encode()
            await send(
                {
                    "type": "http.response.start",
                    "status": 429,
                    "headers": [
                        [b"content-type", b"application/json"],
                        [b"content-length", str(len(body)).encode()],
                        [b"retry-after", b"60"],
                        [b"x-ratelimit-limit", str(limit).encode()],
                        [b"x-ratelimit-remaining", b"0"],
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})
            return

        window.append(now)
        await self.app(scope, receive, send)
