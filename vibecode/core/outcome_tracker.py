from __future__ import annotations

from dataclasses import dataclass, field
from math import prod
from typing import Literal

from vibecode.models import DiagnosticSignal, EditEvent, RevertSignal, TerminalSignal, TestSignal

OutcomeKind = Literal["success", "failure"]


@dataclass
class TrackedEdit:
    edit_event: EditEvent
    deadline_failure_ts: float
    deadline_success_ts: float
    baseline_diagnostics: list[str] = field(default_factory=list)
    baseline_tests: list[str] = field(default_factory=list)
    resolved: bool = False
    was_reverted: bool = False
    reverted_to_text: str = ""
    latest_diagnostic: str = ""
    signal_weights: dict[OutcomeKind, list[float]] = field(default_factory=lambda: {"success": [], "failure": []})


@dataclass
class OutcomeDecision:
    kind: OutcomeKind
    confidence: float
    tracked: TrackedEdit


class OutcomeTracker:
    def __init__(
        self,
        failure_window_sec: int = 180,
        success_window_sec: int = 120,
        min_confidence: float = 0.6,
    ) -> None:
        self.failure_window_sec = failure_window_sec
        self.success_window_sec = success_window_sec
        self.min_confidence = min_confidence
        self._tracked: dict[str, TrackedEdit] = {}

    def track_edit(self, edit_event: EditEvent) -> None:
        self._tracked[edit_event.event_id] = TrackedEdit(
            edit_event=edit_event,
            deadline_failure_ts=edit_event.timestamp + self.failure_window_sec,
            deadline_success_ts=edit_event.timestamp + self.success_window_sec,
        )

    def apply_diagnostic(self, signal: DiagnosticSignal) -> list[OutcomeDecision]:
        decisions: list[OutcomeDecision] = []
        for tracked in self._active_for_file(
            signal.project_path,
            signal.file_path,
            signal.timestamp,
        ):
            tracked.latest_diagnostic = signal.message
            if signal.is_new:
                tracked.signal_weights["failure"].append(0.7)
            if signal.is_resolved:
                tracked.signal_weights["success"].append(0.7)
            decisions.extend(self._collect_decisions(tracked))
        return decisions

    def apply_test(self, signal: TestSignal) -> list[OutcomeDecision]:
        decisions: list[OutcomeDecision] = []
        for tracked in self._active_for_project(signal.project_path, signal.timestamp):
            if signal.status_before == "fail" and signal.status_after == "pass":
                tracked.signal_weights["success"].append(0.9)
            elif signal.status_before == "pass" and signal.status_after == "fail":
                tracked.signal_weights["failure"].append(0.9)
            else:
                continue
            decisions.extend(self._collect_decisions(tracked))
        return decisions

    def apply_revert(self, signal: RevertSignal) -> list[OutcomeDecision]:
        tracked = self._tracked.get(signal.event_id)
        if tracked is None or tracked.resolved:
            return []

        tracked.was_reverted = True
        tracked.reverted_to_text = signal.reverted_to_text
        tracked.signal_weights["failure"].append(0.9)
        return self._collect_decisions(tracked)

    def apply_terminal(self, signal: TerminalSignal) -> list[OutcomeDecision]:
        decisions: list[OutcomeDecision] = []
        lowered = signal.command.lower()
        if not any(term in lowered for term in ("test", "build", "pytest", "npm", "cargo", "go test")):
            return decisions

        for tracked in self._active_for_project(signal.project_path, signal.ended_at):
            if signal.exit_code == 0:
                tracked.signal_weights["success"].append(0.3)
            else:
                tracked.signal_weights["failure"].append(0.4)
            decisions.extend(self._collect_decisions(tracked))
        return decisions

    def _collect_decisions(self, tracked: TrackedEdit) -> list[OutcomeDecision]:
        if tracked.resolved:
            return []

        failure_conf = self._noisy_or(tracked.signal_weights["failure"])
        success_conf = self._noisy_or(tracked.signal_weights["success"])

        if failure_conf < self.min_confidence and success_conf < self.min_confidence:
            return []

        tracked.resolved = True
        if failure_conf >= success_conf:
            return [OutcomeDecision(kind="failure", confidence=failure_conf, tracked=tracked)]
        return [OutcomeDecision(kind="success", confidence=success_conf, tracked=tracked)]

    @staticmethod
    def _noisy_or(weights: list[float]) -> float:
        if not weights:
            return 0.0
        bounded = [min(max(w, 0.0), 1.0) for w in weights]
        return 1.0 - prod(1.0 - w for w in bounded)

    def _active_for_file(self, project_path: str, file_path: str, now_ts: float) -> list[TrackedEdit]:
        self._evict_expired(now_ts)
        items: list[TrackedEdit] = []
        for tracked in self._tracked.values():
            if tracked.resolved:
                continue
            if tracked.edit_event.project_path != project_path:
                continue
            if tracked.edit_event.file_path != file_path:
                continue
            if now_ts > max(tracked.deadline_failure_ts, tracked.deadline_success_ts):
                continue
            items.append(tracked)
        return items

    def _active_for_project(self, project_path: str, now_ts: float) -> list[TrackedEdit]:
        self._evict_expired(now_ts)
        items: list[TrackedEdit] = []
        for tracked in self._tracked.values():
            if tracked.resolved:
                continue
            if tracked.edit_event.project_path != project_path:
                continue
            if now_ts > max(tracked.deadline_failure_ts, tracked.deadline_success_ts):
                continue
            items.append(tracked)
        return items

    def _evict_expired(self, now_ts: float) -> None:
        stale = [
            event_id
            for event_id, tracked in self._tracked.items()
            if now_ts > max(tracked.deadline_failure_ts, tracked.deadline_success_ts)
        ]
        for event_id in stale:
            self._tracked.pop(event_id, None)
