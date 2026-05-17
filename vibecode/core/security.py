from __future__ import annotations

import json
import re
from pathlib import Path


SECRET_PATTERNS = [
    (r"(?i)(OPENAI_API_KEY\s*=\s*)[^\s\n]+", r"\1[REDACTED_SECRET]"),
    (r"(?i)(ANTHROPIC_API_KEY\s*=\s*)[^\s\n]+", r"\1[REDACTED_SECRET]"),
    (r"(?i)(GITHUB_TOKEN\s*=\s*)[^\s\n]+", r"\1[REDACTED_SECRET]"),
    (r"(?i)(GITHUB_PAT\s*=\s*)[^\s\n]+", r"\1[REDACTED_SECRET]"),
    (r"(?i)(AWS_ACCESS_KEY_ID\s*=\s*)[^\s\n]+", r"\1[REDACTED_SECRET]"),
    (r"(?i)(AWS_SECRET_ACCESS_KEY\s*=\s*)[^\s\n]+", r"\1[REDACTED_SECRET]"),
    (r"(?i)(CLOUDFLARE_API_TOKEN\s*=\s*)[^\s\n]+", r"\1[REDACTED_SECRET]"),
    (r"(?i)(DATABASE_URL\s*=\s*)[^\s\n]+", r"\1[REDACTED_SECRET]"),
    (r"(?i)(PASSWORD\s*=\s*)[^\s\n]+", r"\1[REDACTED_SECRET]"),
    (r"(?i)(SECRET\s*=\s*)[^\s\n]+", r"\1[REDACTED_SECRET]"),
    (r"(?i)(PRIVATE\s+KEY)", r"[REDACTED_SECRET]"),
    (r"(?i)(-----BEGIN\s+[^-]+-----).*?(-----END\s+[^-]+-----)", r"[REDACTED_SECRET]"),
    (r"(?i)(sk-[a-zA-Z0-9]{20,})", r"[REDACTED_SECRET]"),
    (r"(?i)(Bearer\s+[a-zA-Z0-9_\-]+)", r"[REDACTED_SECRET]"),
]


def redact_secrets(text: str) -> str:
    if not text:
        return text
    for pattern, replacement in SECRET_PATTERNS:
        text = re.sub(pattern, replacement, text, flags=re.DOTALL)
    return text


class ProjectAllowlist:
    def __init__(self, vibecode_dir: Path) -> None:
        self.vibecode_dir = vibecode_dir
        self._path = vibecode_dir / "allowed_projects.json"
        self._cache: list[str] | None = None

    def _load(self) -> dict:
        if not self._path.exists():
            return {"allowed_projects": []}
        with open(self._path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: dict) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self._cache = None  # invalidate

    def list(self) -> list[str]:
        if self._cache is None:
            self._cache = self._load().get("allowed_projects", [])
        return self._cache

    def add(self, path: str) -> None:
        data = self._load()
        normalized = str(Path(path).resolve())
        if normalized not in data["allowed_projects"]:
            data["allowed_projects"].append(normalized)
            self._save(data)

    def remove(self, path: str) -> None:
        data = self._load()
        normalized = str(Path(path).resolve())
        if normalized in data["allowed_projects"]:
            data["allowed_projects"].remove(normalized)
            self._save(data)

    def is_allowed(self, path: str | None) -> bool:
        if not path:
            return False
        allowed = self.list()
        if not allowed:
            return False
        resolved = Path(path).resolve()
        for a in allowed:
            a_path = Path(a)
            if resolved == a_path or resolved.is_relative_to(a_path):
                return True
        return False
