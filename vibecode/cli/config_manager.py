from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import platformdirs


class ConfigManager:
    """Manages project-level and user-level TOML config."""

    def __init__(self, project_dir: Path | None = None) -> None:
        self.project_dir = project_dir or (Path.cwd() / ".vibecode")
        self.project_config_path = self.project_dir / "config.toml"
        self.user_config_dir = Path(platformdirs.user_config_dir("VibeCode", appauthor=False))
        self.user_config_path = self.user_config_dir / "config.toml"

    def _load_toml(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]
        with open(path, "rb") as f:
            return tomllib.load(f)

    def _save_toml(self, path: Path, data: dict[str, Any]) -> None:
        import tomli_w
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            tomli_w.dump(data, f)

    def read(self) -> dict[str, Any]:
        user = self._load_toml(self.user_config_path)
        project = self._load_toml(self.project_config_path)
        # Project overrides user
        merged = _deep_merge(user, project)
        return merged

    def write_project(self, data: dict[str, Any]) -> None:
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self._save_toml(self.project_config_path, data)

    def write_user(self, data: dict[str, Any]) -> None:
        self.user_config_dir.mkdir(parents=True, exist_ok=True)
        self._save_toml(self.user_config_path, data)

    def set(self, key: str, value: Any, scope: str = "project") -> None:
        path = self.project_config_path if scope == "project" else self.user_config_path
        data = self._load_toml(path)
        keys = key.split(".")
        target = data
        for k in keys[:-1]:
            if k not in target or not isinstance(target[k], dict):
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
        if scope == "project":
            self.write_project(data)
        else:
            self.write_user(data)

    def path(self) -> str:
        if self.project_config_path.exists():
            return str(self.project_config_path)
        if self.user_config_path.exists():
            return str(self.user_config_path)
        return str(self.project_config_path)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
