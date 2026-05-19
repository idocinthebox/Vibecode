from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from vibecode import __version__
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
from vibecode.config.paths import get_vibecode_dir
from vibecode.jobs.confidence_decay import run_once, start_decay_scheduler


def create_app() -> FastAPI:
    app = FastAPI(
        title="VibeCode Local Service",
        version=__version__,
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

    @app.on_event("startup")
    def _start_background_jobs() -> None:
        configured_data_dir = getattr(settings, "data_dir", "")
        base_dir = Path(configured_data_dir) if configured_data_dir else get_vibecode_dir()
        # Eager first pass so decay does not wait the full interval after startup.
        run_once(base_dir)
        start_decay_scheduler(base_dir, interval_hours=settings.confidence_decay_interval_hours)

    return app
