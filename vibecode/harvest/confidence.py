from __future__ import annotations

import math
import re
from datetime import datetime, timezone

from vibecode.harvest.normalizer import CandidateMemory

SOURCE_WEIGHTS: dict[str, float] = {
    "harvest:claude_md": 0.9,
    "harvest:markdown_rule": 0.6,
    "harvest:adr": 0.85,
    "harvest:changelog": 0.7,
    "harvest:linter": 0.55,
    "harvest:inline_comment": 0.5,
}


def recency_from_age_days(age_days: float) -> float:
    return math.exp(-(age_days / 180.0))


def infer_specificity(text: str) -> float:
    lowered = text.lower()
    hints = [
        "python",
        "typescript",
        "javascript",
        "fastapi",
        "pytest",
        "sqlite",
        "postgres",
        "ruff",
        "mypy",
        "api",
        "cli",
    ]
    matches = sum(1 for h in hints if h in lowered)
    base = 0.4 + min(0.6, matches * 0.1)
    if re.search(r"`[^`]+`", text):
        base = min(1.0, base + 0.1)
    return max(0.0, min(1.0, base))


def compute_confidence(source_weight: float, signal_strength: float, age_days: float, specificity: float) -> float:
    recency = recency_from_age_days(age_days)
    score = 0.4 * source_weight + 0.3 * signal_strength + 0.2 * recency + 0.1 * specificity
    return max(0.0, min(1.0, round(score, 4)))


def score_candidate(candidate: CandidateMemory, modified_time_epoch: float, now: datetime | None = None) -> float:
    now_dt = now or datetime.now(timezone.utc)
    modified_dt = datetime.fromtimestamp(modified_time_epoch, tz=timezone.utc)
    age_days = max(0.0, (now_dt - modified_dt).total_seconds() / 86400.0)
    source_weight = SOURCE_WEIGHTS.get(candidate.source_type, 0.6)
    specificity = infer_specificity(candidate.dedupe_text())
    score = compute_confidence(source_weight, candidate.signal_strength, age_days, specificity)
    candidate.confidence = score
    return score
