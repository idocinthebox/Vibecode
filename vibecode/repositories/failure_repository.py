from __future__ import annotations

import json
import sqlite3
from typing import Any

from vibecode.models import FailurePattern


class FailureRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, pattern: FailurePattern) -> None:
        sql = """
        INSERT INTO failure_patterns (
            failure_id, project_id, task_intent, bad_suggestion, failure_reason,
            corrected_approach, prevention_rule, language, framework,
            affected_files_json, tags_json, severity, confidence_score, usage_count,
            source_type, source_ref, source_commit, source_file_path, content_hash,
            is_active, created_at, updated_at, last_used
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(
            sql,
            (
                pattern.failure_id,
                None,
                pattern.task_intent,
                pattern.bad_suggestion,
                pattern.failure_reason,
                pattern.corrected_approach,
                pattern.prevention_rule,
                pattern.language,
                pattern.framework,
                json.dumps(pattern.affected_files),
                json.dumps(pattern.tags),
                pattern.severity,
                pattern.confidence_score,
                pattern.usage_count,
                pattern.source_type,
                pattern.source_ref,
                pattern.source_commit,
                pattern.source_file_path,
                pattern.content_hash,
                1 if pattern.is_active else 0,
                pattern.created_at,
                pattern.updated_at,
                pattern.last_used,
            ),
        )
        self.conn.commit()

    def get_by_id(self, failure_id: str) -> FailurePattern | None:
        row = self.conn.execute(
            "SELECT * FROM failure_patterns WHERE failure_id = ?", (failure_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_pattern(row)

    def list_active(self) -> list[FailurePattern]:
        rows = self.conn.execute(
            "SELECT * FROM failure_patterns WHERE is_active = 1"
        ).fetchall()
        return [self._row_to_pattern(r) for r in rows]

    def search(self, query: str) -> list[FailurePattern]:
        like = f"%{query}%"
        rows = self.conn.execute(
            """
            SELECT * FROM failure_patterns
            WHERE is_active = 1 AND (
                task_intent LIKE ? OR bad_suggestion LIKE ? OR failure_reason LIKE ?
                OR prevention_rule LIKE ? OR language LIKE ? OR framework LIKE ?
                OR tags_json LIKE ? OR affected_files_json LIKE ?
            )
            """,
            (like, like, like, like, like, like, like, like),
        ).fetchall()
        return [self._row_to_pattern(r) for r in rows]

    def update(self, pattern: FailurePattern) -> None:
        sql = """
        UPDATE failure_patterns SET
            task_intent = ?, bad_suggestion = ?, failure_reason = ?,
            corrected_approach = ?, prevention_rule = ?, language = ?, framework = ?,
            affected_files_json = ?, tags_json = ?, severity = ?,
            confidence_score = ?, usage_count = ?, source_type = ?, source_ref = ?,
            source_commit = ?, source_file_path = ?, content_hash = ?,
            is_active = ?, updated_at = ?, last_used = ?
        WHERE failure_id = ?
        """
        self.conn.execute(
            sql,
            (
                pattern.task_intent,
                pattern.bad_suggestion,
                pattern.failure_reason,
                pattern.corrected_approach,
                pattern.prevention_rule,
                pattern.language,
                pattern.framework,
                json.dumps(pattern.affected_files),
                json.dumps(pattern.tags),
                pattern.severity,
                pattern.confidence_score,
                pattern.usage_count,
                pattern.source_type,
                pattern.source_ref,
                pattern.source_commit,
                pattern.source_file_path,
                pattern.content_hash,
                1 if pattern.is_active else 0,
                pattern.updated_at,
                pattern.last_used,
                pattern.failure_id,
            ),
        )
        self.conn.commit()

    def soft_delete(self, failure_id: str) -> None:
        self.conn.execute(
            "UPDATE failure_patterns SET is_active = 0, updated_at = datetime('now') WHERE failure_id = ?",
            (failure_id,),
        )
        self.conn.commit()

    def hard_delete_for_tests_only(self, failure_id: str) -> None:
        self.conn.execute(
            "DELETE FROM failure_patterns WHERE failure_id = ?", (failure_id,)
        )
        self.conn.commit()

    def get_by_content_hash(self, content_hash: str) -> FailurePattern | None:
        row = self.conn.execute(
            "SELECT * FROM failure_patterns WHERE content_hash = ? LIMIT 1",
            (content_hash,),
        ).fetchone()
        if not row:
            return None
        return self._row_to_pattern(row)

    @staticmethod
    def _row_to_pattern(row: sqlite3.Row) -> FailurePattern:
        data = dict(row)
        data["tags"] = json.loads(data.pop("tags_json", "[]"))
        data["affected_files"] = json.loads(data.pop("affected_files_json", "[]"))
        data["is_active"] = bool(data.get("is_active", 1))
        return FailurePattern(**data)
