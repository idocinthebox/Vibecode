from __future__ import annotations

from pathlib import Path

from vibecode.db.sqlite_connection import get_connection
from vibecode.db.sqlite_schema import create_schema
from vibecode.models import AgentProfile
from vibecode.services.capture_service import CaptureService
from vibecode.services.injection_service import InjectionService


def test_inject_prioritizes_failure_warnings(temp_base: Path) -> None:
    conn = get_connection(temp_base)
    create_schema(conn)
    capture = CaptureService(temp_base, conn)
    capture.capture_failure(
        {
            "task_intent": "Fix audio",
            "bad_suggestion": "Use external player",
            "failure_reason": "User wanted embedded",
            "prevention_rule": "Do not use external player",
            "severity": "high",
            "tags": ["audio"],
        }
    )
    capture.add_rule(
        {
            "rule_text": "Always embed media",
            "rule_type": "ui",
            "severity": "high",
            "tags": ["audio"],
        }
    )

    injection = InjectionService(temp_base, conn)
    profile = AgentProfile(
        profile_id="p1",
        name="test",
        target_agent="Test",
        max_context_tokens=2000,
    )
    md = injection.inject("audio", profile)
    assert "# VibeCode Agent Context" in md
    assert "Relevant Failure Warnings" in md
    assert "Relevant Project Rules" in md
    conn.close()


def test_inject_respects_token_budget(temp_base: Path) -> None:
    conn = get_connection(temp_base)
    create_schema(conn)
    capture = CaptureService(temp_base, conn)
    capture.capture_success(
        {
            "name": "Huge pattern",
            "intent_description": "A" * 4000,
            "reasoning_summary": "B" * 4000,
            "tags": ["big"],
        }
    )

    injection = InjectionService(temp_base, conn)
    profile = AgentProfile(
        profile_id="p1",
        name="test",
        target_agent="Test",
        max_context_tokens=100,
    )
    md = injection.inject("big", profile)
    assert "# VibeCode Agent Context" in md
    conn.close()
