from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Literal

MemoryType = Literal["project_rule", "failure_pattern", "success_pattern"]


def normalize_text(text: str) -> str:
    lowered = text.lower()
    without_punct = re.sub(r"[^a-z0-9\s]+", " ", lowered)
    collapsed = re.sub(r"\s+", " ", without_punct).strip()
    return collapsed


def make_source_ref(relative_path: str, line_start: int, line_end: int) -> str:
    return f"{relative_path}#L{line_start}-L{line_end}"


@dataclass(slots=True)
class CandidateMemory:
    memory_type: MemoryType
    title: str
    source_path: str
    line_start: int
    line_end: int
    source_type: str
    extractor: str
    signal_strength: float
    rule_text: str = ""
    rule_type: str = "architecture"
    severity: str = "medium"
    task_intent: str = ""
    bad_suggestion: str = ""
    failure_reason: str = ""
    prevention_rule: str = ""
    corrected_approach: str = ""
    reasoning_summary: str = ""
    code_after: str = ""
    language: str = ""
    framework: str = ""
    tags: list[str] = field(default_factory=list)
    confidence: float = 0.0
    review_state: str = "pending"

    @property
    def source_ref(self) -> str:
        return make_source_ref(self.source_path, self.line_start, self.line_end)

    def dedupe_text(self) -> str:
        if self.memory_type == "project_rule":
            return self.rule_text or self.title
        if self.memory_type == "failure_pattern":
            return "\n".join(
                [
                    self.task_intent,
                    self.bad_suggestion,
                    self.failure_reason,
                    self.prevention_rule,
                ]
            )
        return "\n".join([self.title, self.reasoning_summary, self.code_after])

    def content_hash(self) -> str:
        normalized = normalize_text(self.dedupe_text())
        payload = f"{self.memory_type}|{normalized}".encode()
        return hashlib.sha256(payload).hexdigest()

    def to_preview(self) -> dict[str, object]:
        return {
            "memory_type": self.memory_type,
            "title": self.title,
            "source_type": self.source_type,
            "source_ref": self.source_ref,
            "confidence": self.confidence,
            "review_state": self.review_state,
            "severity": self.severity,
        }
