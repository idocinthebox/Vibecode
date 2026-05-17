from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from vibecode.core.outcome_tracker import TrackedEdit
from vibecode.models import FailurePattern
from vibecode.services.search_service import SearchService
from vibecode.services.token_service import TokenService


class PreventionService:
    def __init__(self, base_dir: Path, conn: sqlite3.Connection | None = None) -> None:
        self.base_dir = Path(base_dir)
        self.conn = conn
        self.search = SearchService(self.base_dir, conn)

    def infer_rule(self, tracked: TrackedEdit) -> str:
        language = tracked.edit_event.language or "this language"
        diagnostic = tracked.latest_diagnostic or "a regression"
        snippet = tracked.edit_event.text_after.strip().splitlines()
        summary = snippet[0][:120] if snippet else "the previous edit pattern"
        return f"Avoid {summary} in {language}; previously caused: {diagnostic}."

    def pre_edit_check(
        self,
        project_path: str,
        file_path: str,
        language: str,
        proposed_text: str,
        task_intent: str | None = None,
        max_matches: int = 5,
        min_confidence: float = 0.5,
    ) -> dict:
        query_parts = [proposed_text, task_intent or "", language, os.path.basename(file_path)]
        query = " ".join(part for part in query_parts if part).strip()
        if not query:
            return {"matches": [], "estimated_tokens_saved": 0}

        matches: list[FailurePattern] = []
        for result in self.search.search(query):
            if result.result_type != "failure":
                continue
            failure = result.obj
            if not isinstance(failure, FailurePattern):
                continue
            confidence = getattr(failure, "confidence", failure.confidence_score)
            if confidence < min_confidence:
                continue
            if getattr(failure, "review_state", "confirmed") == "discarded":
                continue
            matches.append(failure)

        def _sort_key(item: FailurePattern) -> tuple[float, int, float]:
            confidence = float(getattr(item, "confidence", item.confidence_score))
            occurrences = int(getattr(item, "occurrence_count", 1))
            last_seen_raw = getattr(item, "last_seen_at", None) or item.updated_at
            try:
                last_seen = datetime.fromisoformat(last_seen_raw).replace(tzinfo=timezone.utc).timestamp()
            except ValueError:
                last_seen = 0.0
            return (-(confidence * max(occurrences, 1)), -occurrences, -last_seen)

        matches.sort(key=_sort_key)

        payload = []
        estimated_tokens_saved = 0
        for item in matches[:max_matches]:
            prevention = item.prevention_rule or ""
            corrected = item.corrected_approach or ""
            estimated_tokens_saved += TokenService.estimate_tokens(prevention + corrected)
            payload.append(
                {
                    "failure_id": item.failure_id,
                    "prevention_rule": prevention,
                    "corrected_approach": corrected,
                    "confidence": float(getattr(item, "confidence", item.confidence_score)),
                    "last_seen_at": getattr(item, "last_seen_at", None),
                    "occurrence_count": int(getattr(item, "occurrence_count", 1)),
                }
            )

        return {
            "matches": payload,
            "estimated_tokens_saved": estimated_tokens_saved,
        }
