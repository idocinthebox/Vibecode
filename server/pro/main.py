"""Pro Databank Server — FastAPI application entry point.

Run locally:
    uvicorn server.pro.main:app --host 0.0.0.0 --port 8766

Docker:
    See docker-compose.yml for the `pro-server` service.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI

from server.pro.routes.contributions import router as contributions_router
from server.pro.routes.moderation import router as moderation_router
from server.pro.routes.search import router as search_router
from vibecode.api.middleware import RateLimitMiddleware


def create_pro_app(data_dir: str | Path | None = None) -> FastAPI:
    if data_dir is not None:
        os.environ["PRO_DATA_DIR"] = str(data_dir)

    app = FastAPI(
        title="VibeCode Pro Databank",
        version="1.0.0",
        description="Shared pattern databank for VibeCode Pro subscribers.",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(RateLimitMiddleware, default_per_min=60, pre_edit_check_per_min=60)
    app.include_router(contributions_router)
    app.include_router(search_router)
    app.include_router(moderation_router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": "vibecode-pro-databank", "version": "1.0.0"}

    return app


app = create_pro_app()
