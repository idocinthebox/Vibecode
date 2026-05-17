from __future__ import annotations

import sqlite3
from pathlib import Path

from vibecode.models import FailurePattern, ProjectRule, SuccessPattern
from vibecode.repositories.failure_repository import FailureRepository
from vibecode.repositories.pattern_repository import PatternRepository
from vibecode.repositories.rule_repository import RuleRepository
from vibecode.storage.json_store import JsonStore


class ExportService:
    def __init__(self, base_dir: Path, conn: sqlite3.Connection | None = None) -> None:
        self.base_dir = Path(base_dir)
        self.conn = conn
        if conn:
            self.pattern_repo = PatternRepository(conn)
            self.failure_repo = FailureRepository(conn)
            self.rule_repo = RuleRepository(conn)
        else:
            self.pattern_repo = None
            self.failure_repo = None
            self.rule_repo = None
        self.exports_dir = self.base_dir / "exports"
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.success_store = JsonStore(self.base_dir / "success_patterns")
        self.failure_store = JsonStore(self.base_dir / "failure_patterns")
        self.rule_store = JsonStore(self.base_dir / "project_rules")

    def export_all(self) -> list[Path]:
        paths: list[Path] = []
        paths.append(self._export_project_memory())
        paths.append(self._export_failure_bank())
        paths.append(self._export_project_rules())
        paths.append(self._export_agent_context_summary())
        return paths

    def _get_success_patterns(self) -> list[SuccessPattern]:
        if self.pattern_repo:
            return self.pattern_repo.list_active()
        return [
            SuccessPattern.from_json(data)
            for data in self.success_store.load_all()
            if data.get("is_active", True)
        ]

    def _get_failure_patterns(self) -> list[FailurePattern]:
        if self.failure_repo:
            return self.failure_repo.list_active()
        return [
            FailurePattern.from_json(data)
            for data in self.failure_store.load_all()
            if data.get("is_active", True)
        ]

    def _get_project_rules(self) -> list[ProjectRule]:
        if self.rule_repo:
            return self.rule_repo.list_active()
        return [
            ProjectRule.from_json(data)
            for data in self.rule_store.load_all()
            if data.get("is_active", True)
        ]

    def _export_project_memory(self) -> Path:
        lines = ["# Project Memory — Success Patterns", ""]
        for s in self._get_success_patterns():
            lines.append(f"## {s.name}")
            lines.append(f"- **ID:** {s.pattern_id}")
            lines.append(f"- **Intent:** {s.intent_description}")
            lines.append(f"- **Language:** {s.language}")
            lines.append(f"- **Framework:** {s.framework}")
            lines.append(f"- **Tags:** {', '.join(s.tags)}")
            lines.append(f"- **Summary:** {s.reasoning_summary}")
            if s.estimated_tokens_saved:
                lines.append(f"- **Tokens Saved:** ~{s.estimated_tokens_saved}")
            lines.append("")
        path = self.exports_dir / "PROJECT_MEMORY.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def _export_failure_bank(self) -> Path:
        lines = ["# Failure Bank", ""]
        for f in self._get_failure_patterns():
            lines.append(f"## {f.task_intent}")
            lines.append(f"- **ID:** {f.failure_id}")
            lines.append(f"- **Severity:** {f.severity}")
            lines.append(f"- **Bad Suggestion:** {f.bad_suggestion}")
            lines.append(f"- **Why It Failed:** {f.failure_reason}")
            lines.append(f"- **Prevention Rule:** {f.prevention_rule}")
            if f.corrected_approach:
                lines.append(f"- **Corrected Approach:** {f.corrected_approach}")
            lines.append(f"- **Tags:** {', '.join(f.tags)}")
            lines.append("")
        path = self.exports_dir / "FAILURE_BANK.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def _export_project_rules(self) -> Path:
        lines = ["# Project Rules", ""]
        for r in self._get_project_rules():
            lines.append(f"## {r.rule_text}")
            lines.append(f"- **ID:** {r.rule_id}")
            lines.append(f"- **Type:** {r.rule_type}")
            lines.append(f"- **Severity:** {r.severity}")
            lines.append(f"- **Tags:** {', '.join(r.tags)}")
            lines.append("")
        path = self.exports_dir / "PROJECT_RULES.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def _export_agent_context_summary(self) -> Path:
        success_count = len(self._get_success_patterns())
        failure_count = len(self._get_failure_patterns())
        rule_count = len(self._get_project_rules())

        lines = [
            "# Agent Context Summary",
            "",
            f"- **Total Success Patterns:** {success_count}",
            f"- **Total Failure Patterns:** {failure_count}",
            f"- **Total Project Rules:** {rule_count}",
            "",
            "Use `vibecode inject --query <task> --profile <profile>` to generate compact agent context.",
            "",
        ]
        path = self.exports_dir / "AGENT_CONTEXT_SUMMARY.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        return path
