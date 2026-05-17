from __future__ import annotations

import math


class TokenService:
    @staticmethod
    def estimate_tokens(text: str) -> int:
        if not text:
            return 0
        return math.ceil(len(text) / 4)

    @classmethod
    def estimate_tokens_saved(
        cls, original_tokens: int, retrieval_tokens: int
    ) -> int:
        saved = original_tokens - retrieval_tokens
        return max(0, saved)

    @classmethod
    def savings_percent(cls, original_tokens: int, saved_tokens: int) -> float:
        if original_tokens <= 0:
            return 0.0
        return round((saved_tokens / original_tokens) * 100, 2)
