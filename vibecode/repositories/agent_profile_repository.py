from __future__ import annotations

import sqlite3
from typing import Any

from vibecode.models import AgentProfile


class AgentProfileRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, profile: AgentProfile) -> None:
        sql = """
        INSERT INTO agent_profiles (
            profile_id, name, target_agent, max_context_tokens,
            include_success_patterns, include_failure_patterns, include_project_rules,
            include_recent_usage, output_format, template_path, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(
            sql,
            (
                profile.profile_id,
                profile.name,
                profile.target_agent,
                profile.max_context_tokens,
                1 if profile.include_success_patterns else 0,
                1 if profile.include_failure_patterns else 0,
                1 if profile.include_project_rules else 0,
                1 if profile.include_recent_usage else 0,
                profile.output_format,
                profile.template_path,
                profile.created_at,
                profile.updated_at,
            ),
        )
        self.conn.commit()

    def get_by_id(self, profile_id: str) -> AgentProfile | None:
        row = self.conn.execute(
            "SELECT * FROM agent_profiles WHERE profile_id = ?", (profile_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_profile(row)

    def get_by_name(self, name: str) -> AgentProfile | None:
        row = self.conn.execute(
            "SELECT * FROM agent_profiles WHERE name = ?", (name,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_profile(row)

    def list_all(self) -> list[AgentProfile]:
        rows = self.conn.execute("SELECT * FROM agent_profiles").fetchall()
        return [self._row_to_profile(r) for r in rows]

    def update(self, profile: AgentProfile) -> None:
        sql = """
        UPDATE agent_profiles SET
            name = ?, target_agent = ?, max_context_tokens = ?,
            include_success_patterns = ?, include_failure_patterns = ?,
            include_project_rules = ?, include_recent_usage = ?,
            output_format = ?, template_path = ?, updated_at = ?
        WHERE profile_id = ?
        """
        self.conn.execute(
            sql,
            (
                profile.name,
                profile.target_agent,
                profile.max_context_tokens,
                1 if profile.include_success_patterns else 0,
                1 if profile.include_failure_patterns else 0,
                1 if profile.include_project_rules else 0,
                1 if profile.include_recent_usage else 0,
                profile.output_format,
                profile.template_path,
                profile.updated_at,
                profile.profile_id,
            ),
        )
        self.conn.commit()

    def delete(self, profile_id: str) -> None:
        self.conn.execute(
            "DELETE FROM agent_profiles WHERE profile_id = ?", (profile_id,)
        )
        self.conn.commit()

    @staticmethod
    def _row_to_profile(row: sqlite3.Row) -> AgentProfile:
        data = dict(row)
        data["include_success_patterns"] = bool(data.get("include_success_patterns", 1))
        data["include_failure_patterns"] = bool(data.get("include_failure_patterns", 1))
        data["include_project_rules"] = bool(data.get("include_project_rules", 1))
        data["include_recent_usage"] = bool(data.get("include_recent_usage", 0))
        return AgentProfile(**data)
