from __future__ import annotations

from fastapi import FastAPI

from vibecode.api.errors import VibeCodeAPIError, api_error_handler
from vibecode.api.middleware import RateLimitMiddleware
from vibecode.api.routes_harvest import router as harvest_router
from vibecode.api.routes_health import router as health_router
from vibecode.api.routes_memory import router as memory_router
from vibecode.api.routes_observe import router as observe_router
from vibecode.api.routes_pro import router as pro_router
from vibecode.api.routes_review import router as review_router
from vibecode.api.security import LocalhostOnlyMiddleware
from vibecode.config.settings import get_service_settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="VibeCode Local Service",
        version="0.3.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    settings = get_service_settings()
    allow_all = settings.service_host == "0.0.0.0"
    app.add_middleware(LocalhostOnlyMiddleware, allow_all=allow_all)
    app.add_middleware(
        RateLimitMiddleware,
        default_per_min=settings.rate_limit_default_per_min,
        pre_edit_check_per_min=settings.pre_edit_check_rate_limit_per_min,
    )
    app.add_exception_handler(VibeCodeAPIError, api_error_handler)
    app.include_router(health_router)
    app.include_router(memory_router)
    app.include_router(observe_router)
    app.include_router(review_router)
    app.include_router(harvest_router)
    app.include_router(pro_router)
    return app
