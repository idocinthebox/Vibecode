from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal test envs
    from pydantic import BaseModel

    BaseSettings = BaseModel  # type: ignore[misc,assignment]
    SettingsConfigDict = dict  # type: ignore[misc,assignment]


class ServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="VIBECODE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_host: str = "127.0.0.1"
    service_port: int = 8765
    storage_backend: str = "auto"  # auto, sqlite, json, postgres
    project_allowlist: str = ""  # comma-separated paths
    log_level: str = "INFO"
    auto_capture_enabled: bool = True
    auto_capture_failure_window_sec: int = 180
    auto_capture_success_window_sec: int = 120
    auto_capture_min_confidence: float = 0.6
    auto_capture_require_review: bool = True
    pre_edit_check_rate_limit_per_min: int = 30

    @property
    def allowlist_paths(self) -> list[str]:
        if not self.project_allowlist:
            return []
        return [p.strip() for p in self.project_allowlist.split(",") if p.strip()]


@lru_cache
def get_service_settings() -> ServiceSettings:
    return ServiceSettings()
