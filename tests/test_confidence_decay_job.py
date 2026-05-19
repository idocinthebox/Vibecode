"""Tests for Phase 5: Confidence decay background job."""
from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import temp_base


def test_run_once_returns_zero_when_no_db(tmp_path: Path) -> None:
    from vibecode.jobs.confidence_decay import run_once

    result = run_once(tmp_path)
    assert result == 0


def test_run_once_succeeds_with_empty_db(temp_base) -> None:
    from vibecode.db.sqlite_connection import get_connection
    from vibecode.db.sqlite_schema import create_schema
    from vibecode.jobs.confidence_decay import run_once

    conn = get_connection(temp_base)
    create_schema(conn)
    conn.close()

    result = run_once(temp_base)
    assert isinstance(result, int)
    assert result >= 0


def test_start_decay_scheduler_is_idempotent(temp_base) -> None:
    from vibecode.jobs import confidence_decay

    # Reset the module-level flag for isolation
    confidence_decay._scheduler_started = False
    with confidence_decay._scheduler_lock:
        pass  # ensure lock is free

    started_first = confidence_decay.start_decay_scheduler(temp_base, interval_hours=999)
    started_second = confidence_decay.start_decay_scheduler(temp_base, interval_hours=999)
    assert started_first is True
    assert started_second is False
    # Cleanup
    confidence_decay._scheduler_started = False
