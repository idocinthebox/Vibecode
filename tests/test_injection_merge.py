"""Tests for Phase 4: Injection service merge-and-rerank."""

from __future__ import annotations

import uuid

from vibecode.models import FailurePattern
from vibecode.services.injection_service import InjectionService
from vibecode.services.search_service import SearchResult


def _make_result(
    title: str,
    result_type: str = "failure",
    confidence: float = 0.8,
    severity: str = "medium",
    language: str = "python",
) -> SearchResult:
    obj = FailurePattern(
        failure_id=str(uuid.uuid4()),
        task_intent=title,
        bad_suggestion="bad",
        failure_reason="some reason",
        prevention_rule="some rule",
        corrected_approach="",
        language=language,
        severity=severity,
        confidence_score=confidence,
        confidence=confidence,
    )
    return SearchResult(result_type, obj, ["test"])


def test_merge_local_first_boost_prefers_local() -> None:
    local = [_make_result("Local A", confidence=0.7)]
    remote = [_make_result("Remote B", confidence=0.9)]
    merged = InjectionService._merge_and_rerank(local, remote, local_first_boost=0.25)
    # Local A boosted to 0.95 > Remote B at 0.9
    assert merged[0].title == "Local A"
    assert merged[1].title == "Remote B"


def test_merge_deduplicates_by_title() -> None:
    local = [_make_result("SharedTitle", confidence=0.8)]
    remote = [_make_result("SharedTitle", confidence=0.9)]
    merged = InjectionService._merge_and_rerank(local, remote)
    assert len(merged) == 1
    assert merged[0].title == "SharedTitle"


def test_merge_empty_remote_returns_local() -> None:
    local = [_make_result("Local A"), _make_result("Local B")]
    merged = InjectionService._merge_and_rerank(local, [])
    assert len(merged) == 2


def test_merge_empty_local_returns_remote() -> None:
    remote = [_make_result("Remote X"), _make_result("Remote Y")]
    merged = InjectionService._merge_and_rerank([], remote)
    assert len(merged) == 2


def test_merge_sorted_by_score_desc() -> None:
    local = [_make_result("L1", confidence=0.5)]
    remote = [_make_result("R1", confidence=0.95), _make_result("R2", confidence=0.6)]
    # L1 boosted to 0.75, R1 = 0.95, R2 = 0.6
    merged = InjectionService._merge_and_rerank(local, remote, local_first_boost=0.25)
    assert merged[0].title == "R1"
    assert merged[1].title == "L1"
    assert merged[2].title == "R2"


def test_merge_keeps_same_title_with_different_language() -> None:
    local = [_make_result("SharedTitle", language="python")]
    remote = [_make_result("SharedTitle", language="typescript")]

    merged = InjectionService._merge_and_rerank(local, remote)

    assert len(merged) == 2


def test_inject_includes_pro_unavailable_note(tmp_path, monkeypatch) -> None:
    from vibecode.models import AgentProfile

    service = InjectionService(tmp_path)
    monkeypatch.setattr(service.search_service, "search", lambda _query: [])
    service._last_remote_error = "Upstream service unavailable"
    monkeypatch.setattr(service, "_search_remote", lambda _query: [])

    profile = AgentProfile(
        profile_id=str(uuid.uuid4()),
        name="test",
        target_agent="generic",
        max_context_tokens=1000,
        include_success_patterns=True,
        include_failure_patterns=True,
        include_project_rules=True,
    )

    markdown = service.inject("failing command", profile)
    assert "## Pro Databank Unavailable" in markdown
    assert "Upstream service unavailable" in markdown
