from __future__ import annotations

import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from vibecode.config.paths import get_vibecode_dir
from vibecode.config.settings import get_service_settings
from vibecode.core.security import ProjectAllowlist, redact_secrets
from vibecode.db.sqlite_connection import get_connection, get_db_path
from vibecode.models import AgentProfile, FailurePattern, ProjectRule, SuccessPattern
from vibecode.services.capture_service import CaptureService
from vibecode.services.export_service import ExportService
from vibecode.services.hash_service import HashService
from vibecode.services.injection_service import InjectionService
from vibecode.services.search_service import SearchResult, SearchService
from vibecode.services.token_service import TokenService


class VibeCodeService:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or get_vibecode_dir()
        self.allowlist = ProjectAllowlist(self.base_dir)
        self.settings = get_service_settings()
        self._conn: sqlite3.Connection | None = None
        self._capture: CaptureService | None = None
        self._search: SearchService | None = None
        self._inject: InjectionService | None = None
        self._export: ExportService | None = None

    @property
    def conn(self) -> sqlite3.Connection | None:
        if self._conn is None:
            db_path = get_db_path(self.base_dir)
            if db_path.exists():
                self._conn = get_connection(self.base_dir)
        return self._conn

    @property
    def capture(self) -> CaptureService:
        if self._capture is None:
            self._capture = CaptureService(self.base_dir, self.conn)
        return self._capture

    @property
    def search(self) -> SearchService:
        if self._search is None:
            self._search = SearchService(self.base_dir, self.conn)
        return self._search

    @property
    def inject(self) -> InjectionService:
        if self._inject is None:
            self._inject = InjectionService(self.base_dir, self.conn)
        return self._inject

    @property
    def export(self) -> ExportService:
        if self._export is None:
            self._export = ExportService(self.base_dir, self.conn)
        return self._export

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def health_check(self) -> dict[str, Any]:
        db_ok = get_db_path(self.base_dir).exists()
        storage = "sqlite" if db_ok else "json"
        return {
            "status": "ok",
            "version": "0.3.0",
            "storage_backend": storage,
            "database_ok": db_ok,
            "allowed_projects_count": len(self.allowlist.list()),
        }

    def search_memory(
        self,
        query: str,
        project_path: str | None = None,
        language: str | None = None,
        framework: str | None = None,
        include_success_patterns: bool = True,
        include_failure_patterns: bool = True,
        include_project_rules: bool = True,
        max_results: int = 10,
    ) -> dict[str, Any]:
        start = time.time()
        results = self.search.search(query)
        filtered: list[SearchResult] = []
        for r in results:
            if r.result_type == "success" and not include_success_patterns:
                continue
            if r.result_type == "failure" and not include_failure_patterns:
                continue
            if r.result_type == "rule" and not include_project_rules:
                continue
            if language and hasattr(r.obj, "language") and r.obj.language:
                if language.lower() not in r.obj.language.lower():
                    continue
            if framework and hasattr(r.obj, "framework") and r.obj.framework:
                if framework.lower() not in r.obj.framework.lower():
                    continue
            filtered.append(r)
            if len(filtered) >= max_results:
                break

        type_map = {
            "success": "success_pattern",
            "failure": "failure_pattern",
            "rule": "project_rule",
        }
        out: list[dict[str, Any]] = []
        for r in filtered:
            item: dict[str, Any] = {
                "memory_type": type_map.get(r.result_type, r.result_type),
                "memory_id": r.memory_id,
                "title": r.title,
                "summary": r.summary,
                "why_matched": r.why_matched,
            }
            if r.severity:
                item["severity"] = r.severity
            if r.confidence_score is not None:
                item["confidence_score"] = r.confidence_score
            if hasattr(r.obj, "source_type"):
                item["source_type"] = r.obj.source_type
            if hasattr(r.obj, "source_ref"):
                item["source_ref"] = r.obj.source_ref
            out.append(item)

        return {
            "query": query,
            "results": out,
            "retrieval_time_ms": int((time.time() - start) * 1000),
        }

    def inject_context(
        self,
        query: str,
        project_path: str | None = None,
        agent_profile: str = "generic-agent",
        max_context_tokens: int | None = None,
        include_failure_warnings: bool = True,
        include_project_rules: bool = True,
        include_success_patterns: bool = True,
    ) -> dict[str, Any]:
        start = time.time()
        profile_obj = self.capture.get_profile_by_name(agent_profile)
        if profile_obj is None:
            profile_obj = AgentProfile(
                profile_id=str(uuid.uuid4()),
                name=agent_profile,
                target_agent="Generic",
                max_context_tokens=max_context_tokens or 1500,
                include_success_patterns=include_success_patterns,
                include_failure_patterns=include_failure_warnings,
                include_project_rules=include_project_rules,
            )
        if max_context_tokens:
            profile_obj.max_context_tokens = max_context_tokens

        markdown = self.inject.inject(query, profile_obj)
        tokens = TokenService.estimate_tokens(markdown)

        # Count included sections
        included_counts: dict[str, int] = {
            "failure_warnings": markdown.count("## Relevant Failure Warnings"),
            "project_rules": markdown.count("## Relevant Project Rules"),
            "success_patterns": markdown.count("## Relevant Success Patterns"),
        }

        return {
            "context_markdown": markdown,
            "estimated_context_tokens": tokens,
            "estimated_tokens_saved": 0,  # Would need historical lookup
            "included_counts": included_counts,
            "retrieval_time_ms": int((time.time() - start) * 1000),
        }

    def capture_success(
        self,
        project_path: str,
        name: str,
        intent_description: str,
        language: str | None = None,
        framework: str | None = None,
        affected_files: list[str] | None = None,
        original_prompt: str | None = None,
        reasoning_summary: str | None = None,
        code_before: str | None = None,
        code_after: str | None = None,
        diff: str | None = None,
        explanation: str | None = None,
        tags: list[str] | None = None,
        source_type: str = "manual",
        source_ref: str | None = None,
    ) -> dict[str, Any]:
        if not self.allowlist.is_allowed(project_path):
            return self._error("PROJECT_NOT_ALLOWED", project_path)

        data: dict[str, Any] = {
            "name": name,
            "intent_description": intent_description,
            "language": language or "",
            "framework": framework or "",
            "affected_files": affected_files or [],
            "original_prompt": redact_secrets(original_prompt or ""),
            "reasoning_summary": redact_secrets(reasoning_summary or ""),
            "code_before": redact_secrets(code_before or ""),
            "code_after": redact_secrets(code_after or ""),
            "diff": redact_secrets(diff or ""),
            "explanation": redact_secrets(explanation or ""),
            "tags": tags or [],
            "source_type": source_type,
            "source_ref": source_ref or "",
        }
        pattern, created = self.capture.capture_success(data)
        return {
            "pattern_id": pattern.pattern_id,
            "created": created,
            "content_hash": pattern.content_hash,
        }

    def capture_failure(
        self,
        project_path: str,
        task_intent: str,
        bad_suggestion: str,
        failure_reason: str,
        prevention_rule: str,
        corrected_approach: str | None = None,
        language: str | None = None,
        framework: str | None = None,
        affected_files: list[str] | None = None,
        severity: str = "medium",
        tags: list[str] | None = None,
        source_type: str = "manual",
        source_ref: str | None = None,
    ) -> dict[str, Any]:
        if not self.allowlist.is_allowed(project_path):
            return self._error("PROJECT_NOT_ALLOWED", project_path)

        data: dict[str, Any] = {
            "task_intent": task_intent,
            "bad_suggestion": redact_secrets(bad_suggestion),
            "failure_reason": redact_secrets(failure_reason),
            "prevention_rule": redact_secrets(prevention_rule),
            "corrected_approach": redact_secrets(corrected_approach or ""),
            "language": language or "",
            "framework": framework or "",
            "affected_files": affected_files or [],
            "severity": severity,
            "tags": tags or [],
            "source_type": source_type,
            "source_ref": source_ref or "",
        }
        pattern, created = self.capture.capture_failure(data)
        return {
            "failure_id": pattern.failure_id,
            "created": created,
            "content_hash": pattern.content_hash,
        }

    def add_project_rule(
        self,
        project_path: str,
        rule_text: str,
        rule_type: str,
        severity: str = "medium",
        tags: list[str] | None = None,
        source_type: str = "manual",
        source_ref: str | None = None,
    ) -> dict[str, Any]:
        if not self.allowlist.is_allowed(project_path):
            return self._error("PROJECT_NOT_ALLOWED", project_path)

        data: dict[str, Any] = {
            "rule_text": redact_secrets(rule_text),
            "rule_type": rule_type,
            "severity": severity,
            "tags": tags or [],
            "source_type": source_type,
            "source_ref": source_ref or "",
        }
        rule = self.capture.add_rule(data)
        return {
            "rule_id": rule.rule_id,
            "created": True,
        }

    def get_token_report(self, project_path: str | None = None, days: int = 30) -> dict[str, Any]:
        # Simple report from local data
        if self.conn:
            cursor = self.conn.execute(
                "SELECT COUNT(*) AS c FROM success_patterns WHERE is_active = 1"
            )
            success_count = cursor.fetchone()["c"]
            cursor = self.conn.execute(
                "SELECT COUNT(*) AS c FROM failure_patterns WHERE is_active = 1"
            )
            failure_count = cursor.fetchone()["c"]
            cursor = self.conn.execute(
                "SELECT COUNT(*) AS c FROM project_rules WHERE is_active = 1"
            )
            rule_count = cursor.fetchone()["c"]
            cursor = self.conn.execute(
                "SELECT COALESCE(SUM(estimated_tokens_saved), 0) AS total FROM success_patterns WHERE is_active = 1"
            )
            total_saved = cursor.fetchone()["total"]
        else:
            from vibecode.storage.json_store import JsonStore
            success_store = JsonStore(self.base_dir / "success_patterns")
            failure_store = JsonStore(self.base_dir / "failure_patterns")
            rule_store = JsonStore(self.base_dir / "project_rules")
            success_count = success_store.count()
            failure_count = failure_store.count()
            rule_count = rule_store.count()
            total_saved = sum(
                d.get("estimated_tokens_saved", 0)
                for d in success_store.load_all()
            )

        return {
            "success_patterns": success_count,
            "failure_patterns": failure_count,
            "project_rules": rule_count,
            "estimated_tokens_saved": total_saved,
            "days": days,
        }

    @staticmethod
    def _error(code: str, project_path: str | None = None) -> dict[str, Any]:
        messages = {
            "PROJECT_NOT_ALLOWED": (
                "The project path is not in the VibeCode allowlist.",
                "Run: vibecode project allow <path>",
            ),
            "STORAGE_NOT_INITIALIZED": (
                "No VibeCode memory store was found.",
                "Run: vibecode init or vibecode init-db",
            ),
        }
        msg, fix = messages.get(code, ("Unknown error.", ""))
        result: dict[str, Any] = {"error": code, "message": msg, "fix": fix}
        if project_path:
            result["project_path"] = project_path
        return result
