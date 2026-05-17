from __future__ import annotations

import hashlib

from vibecode.models import FailurePattern, SuccessPattern


class HashService:
    @staticmethod
    def hash_text(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @classmethod
    def hash_success_pattern(cls, pattern: SuccessPattern) -> str:
        payload = "\n".join(
            [
                pattern.name,
                pattern.intent_description,
                pattern.language,
                pattern.framework,
                pattern.reasoning_summary,
                pattern.code_after,
            ]
        )
        return cls.hash_text(payload)

    @classmethod
    def hash_failure_pattern(cls, pattern: FailurePattern) -> str:
        payload = "\n".join(
            [
                pattern.task_intent,
                pattern.bad_suggestion,
                pattern.failure_reason,
                pattern.prevention_rule,
            ]
        )
        return cls.hash_text(payload)
