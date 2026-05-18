from __future__ import annotations

from pathlib import Path

from vibecode.core.memory_service import VibeCodeService
from vibecode.core.security import ProjectAllowlist
from vibecode.db.audit_log_repository import AuditLogRepository
from vibecode.db.sqlite_connection import get_connection
from vibecode.db.sqlite_schema import create_schema


def _bootstrap_base(temp_base: Path) -> Path:
    base = temp_base / ".vibecode"
    base.mkdir()
    for sub in ("success_patterns", "failure_patterns", "project_rules", "agent_profiles"):
        (base / sub).mkdir()
    (base / "config.json").write_text('{"version":"0.1.0"}')
    conn = get_connection(base)
    create_schema(conn)
    conn.close()
    return base


def test_capture_success_emits_audit_row(temp_base: Path) -> None:
    base = _bootstrap_base(temp_base)
    allowlist = ProjectAllowlist(base)
    project = str(temp_base)
    allowlist.add(project)

    svc = VibeCodeService(base)
    try:
        result = svc.capture_success(
            project_path=project,
            name="Audit test",
            intent_description="Verify audit logging",
        )
        assert "pattern_id" in result

        audit = AuditLogRepository(svc.conn)
        rows = audit.list_by_action("memory.capture_success")
        assert rows, "capture_success must emit an audit row"
        assert rows[0]["target_id"] == result["pattern_id"]
        assert rows[0]["project_path"] == project
    finally:
        if svc.conn:
            svc.conn.close()


def test_observe_edit_emits_audit_row(temp_base: Path) -> None:
    base = _bootstrap_base(temp_base)
    allowlist = ProjectAllowlist(base)
    project = str(temp_base)
    allowlist.add(project)

    svc = VibeCodeService(base)
    try:
        svc.observe_edit(
            {
                "event_id": "evt-audit-1",
                "project_path": project,
                "file_path": str(temp_base / "a.py"),
                "language": "python",
                "agent_source": "agent:GitHub.copilot",
                "range": {
                    "start_line": 0,
                    "start_character": 0,
                    "end_line": 0,
                    "end_character": 0,
                },
                "text_before": "a = 1",
                "text_after": "a = 2",
                "timestamp": 1000.0,
                "document_version": 1,
            }
        )

        audit = AuditLogRepository(svc.conn)
        rows = audit.list_by_action("observe.edit")
        assert rows, "observe_edit must emit an audit row"
        assert rows[0]["target_id"] == "evt-audit-1"
        assert rows[0]["meta"]["file_path"].endswith("a.py")
    finally:
        if svc.conn:
            svc.conn.close()


def test_search_memory_emits_audit_row(temp_base: Path) -> None:
    base = _bootstrap_base(temp_base)
    svc = VibeCodeService(base)
    try:
        svc.search_memory(query="hello world", max_results=5)
        audit = AuditLogRepository(svc.conn)
        rows = audit.list_by_action("memory.search")
        assert rows, "search_memory must emit an audit row"
    finally:
        if svc.conn:
            svc.conn.close()
