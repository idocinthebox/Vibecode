from __future__ import annotations

import json
import sqlite3
from typing import Any

from vibecode.models import SuccessPattern


class PatternRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, pattern: SuccessPattern) -> None:
        sql = """
        INSERT INTO success_patterns (
            pattern_id, project_id, name, intent_description, language, framework, file_type,
            tags_json, affected_files_json, original_prompt, reasoning_summary, reasoning_steps_json,
            code_before, code_after, diff, explanation,
            token_cost_original, token_cost_retrieval, estimated_tokens_saved,
            confidence_score, usage_count, success_rate,
            source_type, source_ref, source_commit, source_file_path, content_hash,
            is_active, created_at, updated_at, last_used
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(
            sql,
            (
                pattern.pattern_id,
                None,
                pattern.name,
                pattern.intent_description,
                pattern.language,
                pattern.framework,
                pattern.file_type,
                json.dumps(pattern.tags),
                json.dumps(pattern.affected_files),
                pattern.original_prompt,
                pattern.reasoning_summary,
                json.dumps(pattern.reasoning_steps),
                pattern.code_before,
                pattern.code_after,
                pattern.diff,
                pattern.explanation,
                pattern.token_cost_original,
                pattern.token_cost_retrieval,
                pattern.estimated_tokens_saved,
                pattern.confidence_score,
                pattern.usage_count,
                pattern.success_rate,
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

    def get_by_id(self, pattern_id: str) -> SuccessPattern | None:
        row = self.conn.execute(
            "SELECT * FROM success_patterns WHERE pattern_id = ?", (pattern_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_pattern(row)

    def list_active(self) -> list[SuccessPattern]:
        rows = self.conn.execute(
            "SELECT * FROM success_patterns WHERE is_active = 1"
        ).fetchall()
        return [self._row_to_pattern(r) for r in rows]

    def search(self, query: str) -> list[SuccessPattern]:
        like = f"%{query}%"
        rows = self.conn.execute(
            """
            SELECT * FROM success_patterns
            WHERE is_active = 1 AND (
                name LIKE ? OR intent_description LIKE ? OR language LIKE ?
                OR framework LIKE ? OR reasoning_summary LIKE ?
                OR tags_json LIKE ? OR affected_files_json LIKE ?
            )
            """,
            (like, like, like, like, like, like, like),
        ).fetchall()
        return [self._row_to_pattern(r) for r in rows]

    def update(self, pattern: SuccessPattern) -> None:
        sql = """
        UPDATE success_patterns SET
            name = ?, intent_description = ?, language = ?, framework = ?, file_type = ?,
            tags_json = ?, affected_files_json = ?, original_prompt = ?, reasoning_summary = ?,
            reasoning_steps_json = ?, code_before = ?, code_after = ?, diff = ?, explanation = ?,
            token_cost_original = ?, token_cost_retrieval = ?, estimated_tokens_saved = ?,
            confidence_score = ?, usage_count = ?, success_rate = ?,
            source_type = ?, source_ref = ?, source_commit = ?, source_file_path = ?, content_hash = ?,
            is_active = ?, updated_at = ?, last_used = ?
        WHERE pattern_id = ?
        """
        self.conn.execute(
            sql,
            (
                pattern.name,
                pattern.intent_description,
                pattern.language,
                pattern.framework,
                pattern.file_type,
                json.dumps(pattern.tags),
                json.dumps(pattern.affected_files),
                pattern.original_prompt,
                pattern.reasoning_summary,
                json.dumps(pattern.reasoning_steps),
                pattern.code_before,
                pattern.code_after,
                pattern.diff,
                pattern.explanation,
                pattern.token_cost_original,
                pattern.token_cost_retrieval,
                pattern.estimated_tokens_saved,
                pattern.confidence_score,
                pattern.usage_count,
                pattern.success_rate,
                pattern.source_type,
                pattern.source_ref,
                pattern.source_commit,
                pattern.source_file_path,
                pattern.content_hash,
                1 if pattern.is_active else 0,
                pattern.updated_at,
                pattern.last_used,
                pattern.pattern_id,
            ),
        )
        self.conn.commit()

    def soft_delete(self, pattern_id: str) -> None:
        self.conn.execute(
            "UPDATE success_patterns SET is_active = 0, updated_at = datetime('now') WHERE pattern_id = ?",
            (pattern_id,),
        )
        self.conn.commit()

    def hard_delete_for_tests_only(self, pattern_id: str) -> None:
        self.conn.execute(
            "DELETE FROM success_patterns WHERE pattern_id = ?", (pattern_id,)
        )
        self.conn.commit()

    def get_by_content_hash(self, content_hash: str) -> SuccessPattern | None:
        row = self.conn.execute(
            "SELECT * FROM success_patterns WHERE content_hash = ? LIMIT 1",
            (content_hash,),
        ).fetchone()
        if not row:
            return None
        return self._row_to_pattern(row)

    @staticmethod
    def _row_to_pattern(row: sqlite3.Row) -> SuccessPattern:
        data = dict(row)
        data["tags"] = json.loads(data.pop("tags_json", "[]"))
        data["affected_files"] = json.loads(data.pop("affected_files_json", "[]"))
        data["reasoning_steps"] = json.loads(data.pop("reasoning_steps_json", "[]"))
        data["is_active"] = bool(data.get("is_active", 1))
        return SuccessPattern(**data)
