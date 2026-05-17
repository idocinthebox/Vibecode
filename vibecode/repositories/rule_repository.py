from __future__ import annotations

import json
import sqlite3
from typing import Any

from vibecode.models import ProjectRule


class RuleRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, rule: ProjectRule) -> None:
        sql = """
        INSERT INTO project_rules (
            rule_id, project_id, rule_text, rule_type, severity,
            source_success_pattern_id, source_failure_id, tags_json,
            is_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(
            sql,
            (
                rule.rule_id,
                None,
                rule.rule_text,
                rule.rule_type,
                rule.severity,
                rule.source_success_pattern_id,
                rule.source_failure_id,
                json.dumps(rule.tags),
                1 if rule.is_active else 0,
                rule.created_at,
                rule.updated_at,
            ),
        )
        self.conn.commit()

    def get_by_id(self, rule_id: str) -> ProjectRule | None:
        row = self.conn.execute(
            "SELECT * FROM project_rules WHERE rule_id = ?", (rule_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_rule(row)

    def list_active(self) -> list[ProjectRule]:
        rows = self.conn.execute(
            "SELECT * FROM project_rules WHERE is_active = 1"
        ).fetchall()
        return [self._row_to_rule(r) for r in rows]

    def search(self, query: str) -> list[ProjectRule]:
        like = f"%{query}%"
        rows = self.conn.execute(
            """
            SELECT * FROM project_rules
            WHERE is_active = 1 AND (
                rule_text LIKE ? OR rule_type LIKE ? OR tags_json LIKE ?
            )
            """,
            (like, like, like),
        ).fetchall()
        return [self._row_to_rule(r) for r in rows]

    def update(self, rule: ProjectRule) -> None:
        sql = """
        UPDATE project_rules SET
            rule_text = ?, rule_type = ?, severity = ?,
            source_success_pattern_id = ?, source_failure_id = ?, tags_json = ?,
            is_active = ?, updated_at = ?
        WHERE rule_id = ?
        """
        self.conn.execute(
            sql,
            (
                rule.rule_text,
                rule.rule_type,
                rule.severity,
                rule.source_success_pattern_id,
                rule.source_failure_id,
                json.dumps(rule.tags),
                1 if rule.is_active else 0,
                rule.updated_at,
                rule.rule_id,
            ),
        )
        self.conn.commit()

    def soft_delete(self, rule_id: str) -> None:
        self.conn.execute(
            "UPDATE project_rules SET is_active = 0, updated_at = datetime('now') WHERE rule_id = ?",
            (rule_id,),
        )
        self.conn.commit()

    def hard_delete_for_tests_only(self, rule_id: str) -> None:
        self.conn.execute(
            "DELETE FROM project_rules WHERE rule_id = ?", (rule_id,)
        )
        self.conn.commit()

    @staticmethod
    def _row_to_rule(row: sqlite3.Row) -> ProjectRule:
        data = dict(row)
        data["tags"] = json.loads(data.pop("tags_json", "[]"))
        data["is_active"] = bool(data.get("is_active", 1))
        return ProjectRule(**data)
