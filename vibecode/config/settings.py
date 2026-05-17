from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    @property
    def allowlist_paths(self) -> list[str]:
        if not self.project_allowlist:
            return []
        return [p.strip() for p in self.project_allowlist.split(",") if p.strip()]


@lru_cache
def get_service_settings() -> ServiceSettings:
    return ServiceSettings()
