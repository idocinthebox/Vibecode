from __future__ import annotations

from pathlib import Path

from vibecode.db.audit_log_repository import AuditLogRepository
from vibecode.db.sqlite_connection import get_connection
from vibecode.db.sqlite_schema import create_schema


def test_audit_log_record_and_query(temp_base: Path) -> None:
    conn = get_connection(temp_base)
    create_schema(conn)

    repo = AuditLogRepository(conn)
    entry_id = repo.record(
        actor="agent:test",
        action="memory.capture_success",
        target_type="success_pattern",
        target_id="sp-123",
        project_path="/tmp/project",
        meta={"created": True},
    )

    assert entry_id

    by_actor = repo.list_by_actor("agent:test")
    assert by_actor
    assert by_actor[0]["id"] == entry_id
    assert by_actor[0]["meta"]["created"] is True

    by_action = repo.list_by_action("memory.capture_success")
    assert by_action
    assert by_action[0]["id"] == entry_id

    by_target = repo.list_by_target("success_pattern", "sp-123")
    assert by_target
    assert by_target[0]["id"] == entry_id

    conn.close()
