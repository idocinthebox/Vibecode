from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from vibecode.core.outcome_tracker import TrackedEdit
from vibecode.core.prevention_service import PreventionService
from vibecode.services.capture_service import CaptureService


class AutoCaptureService:
    def __init__(
        self,
        capture: CaptureService,
        prevention: PreventionService,
        require_review: bool = True,
    ) -> None:
        self.capture = capture
        self.prevention = prevention
        self.require_review = require_review

    def on_outcome(
        self,
        tracked: TrackedEdit,
        kind: Literal["success", "failure"],
        confidence: float,
    ) -> dict:
        payload = self._build_payload(tracked, confidence)
        review_state = "pending" if self.require_review else "confirmed"
        source_type = f"auto:{tracked.edit_event.agent_source}"

        if kind == "success":
            pattern, created = self.capture.capture_success(
                {
                    **payload,
                    "name": self._success_name(tracked),
                    "intent_description": "Automatically captured successful agent edit",
                    "reasoning_summary": "Agent edit correlated with improved outcomes.",
                    "source_type": source_type,
                    "review_state": review_state,
                }
            )
            return {
                "kind": "success_pattern",
                "memory_id": pattern.pattern_id,
                "created": created,
                "confidence": confidence,
            }

        failure_reason = tracked.latest_diagnostic or "Agent edit introduced a regression."
        corrected = tracked.reverted_to_text if tracked.was_reverted else ""
        prevention_rule = self.prevention.infer_rule(tracked)
        pattern, created = self.capture.capture_failure(
            {
                **payload,
                "task_intent": "Automatically captured failed agent edit",
                "bad_suggestion": tracked.edit_event.text_after,
                "failure_reason": failure_reason,
                "prevention_rule": prevention_rule,
                "corrected_approach": corrected,
                "severity": self._severity_from_confidence(confidence),
                "source_type": source_type,
                "review_state": review_state,
            }
        )
        return {
            "kind": "failure_pattern",
            "memory_id": pattern.failure_id,
            "created": created,
            "confidence": confidence,
        }

    def _build_payload(self, tracked: TrackedEdit, confidence: float) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "language": tracked.edit_event.language,
            "affected_files": [tracked.edit_event.file_path],
            "code_before": tracked.edit_event.text_before,
            "code_after": tracked.edit_event.text_after,
            "tags": ["auto-capture", "agent-feedback-loop"],
            "confidence": confidence,
            "occurrence_count": 1,
            "last_seen_at": now,
            "agent_source": tracked.edit_event.agent_source,
            "created_at": now,
            "updated_at": now,
        }

    @staticmethod
    def _success_name(tracked: TrackedEdit) -> str:
        filename = tracked.edit_event.file_path.split("/")[-1].split("\\")[-1]
        return f"Auto success: {filename}"

    @staticmethod
    def _severity_from_confidence(confidence: float) -> str:
        if confidence >= 0.9:
            return "critical"
        if confidence >= 0.75:
            return "high"
        if confidence >= 0.5:
            return "medium"
        return "low"
