from __future__ import annotations

import pytest

from tests.postgres.conftest import PG_AVAILABLE
from vibecode.db.models import (
    AgentProfile,
    Project,
    UsageEvent,
    User,
)
from vibecode.db.repositories import (
    PostgresAgentProfileRepository,
    PostgresUsageRepository,
)

pytestmark = pytest.mark.skipif(not PG_AVAILABLE, reason="PostgreSQL not available")


def test_create_user(pg_session) -> None:
    user = User(username="testuser", email="test@example.com")
    pg_session.add(user)
    pg_session.commit()
    pg_session.refresh(user)
    assert user.id is not None
    assert user.user_id is not None


def test_create_project(pg_session) -> None:
    user = User(username="projectowner", email="po@example.com")
    pg_session.add(user)
    pg_session.commit()
    project = Project(name="Test Project", owner_id=user.id)
    pg_session.add(project)
    pg_session.commit()
    pg_session.refresh(project)
    assert project.id is not None
    assert project.project_id is not None


def test_create_agent_profile(pg_session) -> None:
    repo = PostgresAgentProfileRepository(pg_session)
    profile = AgentProfile(
        name="opus-review",
        target_agent="Claude Opus",
        max_context_tokens=1800,
    )
    created = repo.create(profile)
    assert created.id is not None
    assert created.profile_id is not None


def test_usage_event_created(pg_session) -> None:
    import uuid
    from datetime import datetime, timezone

    repo = PostgresUsageRepository(pg_session)
    event = UsageEvent(
        event_id=uuid.uuid4(),
        memory_type="success_pattern",
        memory_id=uuid.uuid4(),
        tokens_saved=120,
        query_text="test query",
        agent_profile="codex-build",
    )
    pg_session.add(event)
    pg_session.commit()
    pg_session.refresh(event)
    assert event.id is not None

    total = repo.total_tokens_saved()
    assert total == 120


def test_vector_extension_available(pg_engine) -> None:
    with pg_engine.connect() as conn:
        result = conn.execute(
            "SELECT extname FROM pg_extension WHERE extname = 'vector'"
        )
        assert result.scalar() == "vector"
