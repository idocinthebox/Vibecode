from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


class JsonStore:
    """Generic JSON file store for a single entity type."""

    def __init__(self, directory: Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, entity_id: str) -> Path:
        return self.directory / f"{entity_id}.json"

    def save(self, entity_id: str, data: dict[str, Any]) -> Path:
        path = self._path(entity_id)
        tmp_fd, tmp_path = tempfile.mkstemp(dir=self.directory, suffix=".tmp")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
        return path

    def load(self, entity_id: str) -> dict[str, Any] | None:
        path = self._path(entity_id)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_all(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for filename in os.listdir(self.directory):
            if not filename.endswith(".json"):
                continue
            path = self.directory / filename
            with open(path, "r", encoding="utf-8") as f:
                results.append(json.load(f))
        return results

    def exists(self, entity_id: str) -> bool:
        return self._path(entity_id).exists()

    def delete(self, entity_id: str) -> bool:
        path = self._path(entity_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def count(self) -> int:
        return len([f for f in os.listdir(self.directory) if f.endswith(".json")])
