from __future__ import annotations

import sqlite3
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from vibecode.config.paths import get_vibecode_dir
from vibecode.config.settings import get_service_settings
from vibecode.core.auto_capture_service import AutoCaptureService
from vibecode.core.edit_attribution import normalize_agent_source
from vibecode.core.health_service import decay_confidence
from vibecode.core.outcome_tracker import OutcomeTracker
from vibecode.core.prevention_service import PreventionService
from vibecode.core.security import ProjectAllowlist, redact_secrets
from vibecode.db.audit_log_repository import AuditLogRepository
from vibecode.db.sqlite_connection import get_connection, get_db_path
from vibecode.models import (
    AgentProfile,
    DiagnosticSignal,
    EditEvent,
    FailurePattern,
    ProjectRule,
    RevertSignal,
    SuccessPattern,
    TerminalSignal,
    TestSignal,
)
from vibecode.repositories.usage_repository import UsageRepository
from vibecode.services.capture_service import CaptureService
from vibecode.services.export_service import ExportService
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
        self._prevention: PreventionService | None = None
        self._outcome_tracker = OutcomeTracker(
            failure_window_sec=self.settings.auto_capture_failure_window_sec,
            success_window_sec=self.settings.auto_capture_success_window_sec,
            min_confidence=self.settings.auto_capture_min_confidence,
        )
        self._auto_capture: AutoCaptureService | None = None
        self._pre_edit_check_calls: dict[str, deque[float]] = defaultdict(deque)

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

    @property
    def prevention(self) -> PreventionService:
        if self._prevention is None:
            self._prevention = PreventionService(self.base_dir, self.conn)
        return self._prevention

    @property
    def auto_capture(self) -> AutoCaptureService:
        if self._auto_capture is None:
            self._auto_capture = AutoCaptureService(
                capture=self.capture,
                prevention=self.prevention,
                require_review=self.settings.auto_capture_require_review,
            )
        return self._auto_capture

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _audit(
        self,
        actor: str,
        action: str,
        target_type: str,
        target_id: str,
        project_path: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> None:
        if self.conn is None:
            return
        try:
            AuditLogRepository(self.conn).record(
                actor=actor,
                action=action,
                target_type=target_type,
                target_id=target_id,
                project_path=project_path,
                meta=meta,
            )
        except Exception:
            # Audit logging must never break primary memory operations.
            return

    def health_check(self) -> dict[str, Any]:
        db_ok = get_db_path(self.base_dir).exists()
        storage = "sqlite" if db_ok else "json"
        decayed = 0
        if self.conn is not None:
            decayed = decay_confidence(self.conn)
        return {
            "status": "ok",
            "version": "0.3.0",
            "storage_backend": storage,
            "database_ok": db_ok,
            "allowed_projects_count": len(self.allowlist.list()),
            "decayed_confidence_patterns": decayed,
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
            if r.result_type == "failure" and hasattr(r.obj, "corrected_approach"):
                item["corrected_approach"] = r.obj.corrected_approach
            out.append(item)

        self._audit(
            actor="api",
            action="memory.search",
            target_type="query",
            target_id=redact_secrets(query)[:120],
            project_path=project_path,
            meta={
                "result_count": len(out),
                "include_success_patterns": include_success_patterns,
                "include_failure_patterns": include_failure_patterns,
                "include_project_rules": include_project_rules,
                "language": language,
                "framework": framework,
                "max_results": max_results,
            },
        )

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

        self._audit(
            actor=profile_obj.name,
            action="memory.inject",
            target_type="query",
            target_id=redact_secrets(query)[:120],
            project_path=project_path,
            meta={
                "agent_profile": profile_obj.name,
                "max_context_tokens": profile_obj.max_context_tokens,
                "estimated_context_tokens": tokens,
                "included_counts": included_counts,
            },
        )

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
        confidence: float | None = None,
        occurrence_count: int | None = None,
        last_seen_at: str | None = None,
        agent_source: str | None = None,
        review_state: str | None = None,
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
            "confidence": confidence if confidence is not None else 1.0,
            "occurrence_count": occurrence_count if occurrence_count is not None else 1,
            "last_seen_at": last_seen_at or self._now(),
            "agent_source": normalize_agent_source(agent_source or ""),
            "review_state": review_state or "confirmed",
        }
        pattern, created = self.capture.capture_success(data)
        self._audit(
            actor=data["agent_source"] or "manual",
            action="memory.capture_success",
            target_type="success_pattern",
            target_id=pattern.pattern_id,
            project_path=project_path,
            meta={
                "created": created,
                "source_type": data["source_type"],
                "review_state": data["review_state"],
            },
        )
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
        confidence: float | None = None,
        occurrence_count: int | None = None,
        last_seen_at: str | None = None,
        agent_source: str | None = None,
        review_state: str | None = None,
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
            "confidence": confidence if confidence is not None else 1.0,
            "occurrence_count": occurrence_count if occurrence_count is not None else 1,
            "last_seen_at": last_seen_at or self._now(),
            "agent_source": normalize_agent_source(agent_source or ""),
            "review_state": review_state or "confirmed",
        }
        pattern, created = self.capture.capture_failure(data)
        self._audit(
            actor=data["agent_source"] or "manual",
            action="memory.capture_failure",
            target_type="failure_pattern",
            target_id=pattern.failure_id,
            project_path=project_path,
            meta={
                "created": created,
                "severity": data["severity"],
                "source_type": data["source_type"],
                "review_state": data["review_state"],
            },
        )
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
        self._audit(
            actor="manual",
            action="memory.add_rule",
            target_type="project_rule",
            target_id=rule.rule_id,
            project_path=project_path,
            meta={
                "rule_type": rule.rule_type,
                "severity": rule.severity,
                "source_type": rule.source_type,
            },
        )
        return {
            "rule_id": rule.rule_id,
            "created": True,
        }

    def get_token_report(self, project_path: str | None = None, days: int = 30) -> dict[str, Any]:
        # Simple report from local data
        if self.conn:
            cursor = self.conn.execute("SELECT COUNT(*) AS c FROM success_patterns WHERE is_active = 1")
            success_count = cursor.fetchone()["c"]
            cursor = self.conn.execute("SELECT COUNT(*) AS c FROM failure_patterns WHERE is_active = 1")
            failure_count = cursor.fetchone()["c"]
            cursor = self.conn.execute("SELECT COUNT(*) AS c FROM project_rules WHERE is_active = 1")
            rule_count = cursor.fetchone()["c"]
            cursor = self.conn.execute(
                "SELECT COALESCE(SUM(estimated_tokens_saved), 0) AS total FROM success_patterns WHERE is_active = 1"
            )
            total_saved = cursor.fetchone()["total"]
            cursor = self.conn.execute(
                "SELECT COUNT(*) AS c FROM success_patterns WHERE is_active = 1 AND source_type LIKE 'auto:%'"
            )
            auto_success = cursor.fetchone()["c"]
            cursor = self.conn.execute(
                "SELECT COUNT(*) AS c FROM failure_patterns WHERE is_active = 1 AND source_type LIKE 'auto:%'"
            )
            auto_failure = cursor.fetchone()["c"]
            cursor = self.conn.execute("SELECT COUNT(*) AS c FROM usage_events WHERE memory_type = 'prevention_hit'")
            prevention_hits = cursor.fetchone()["c"]
            cursor = self.conn.execute(
                "SELECT COALESCE(SUM(tokens_saved), 0) AS total FROM usage_events WHERE memory_type = 'prevention_hit'"
            )
            auto_saved_from_prevention = cursor.fetchone()["total"]
            cursor = self.conn.execute(
                "SELECT COALESCE(SUM(estimated_tokens_saved), 0) AS total FROM success_patterns WHERE is_active = 1 AND source_type LIKE 'auto:%'"
            )
            auto_saved_from_success = cursor.fetchone()["total"]
            estimated_tokens_saved_auto = auto_saved_from_prevention + auto_saved_from_success
        else:
            from vibecode.storage.json_store import JsonStore

            success_store = JsonStore(self.base_dir / "success_patterns")
            failure_store = JsonStore(self.base_dir / "failure_patterns")
            rule_store = JsonStore(self.base_dir / "project_rules")
            success_count = success_store.count()
            failure_count = failure_store.count()
            rule_count = rule_store.count()
            total_saved = sum(d.get("estimated_tokens_saved", 0) for d in success_store.load_all())
            auto_success = sum(1 for d in success_store.load_all() if str(d.get("source_type", "")).startswith("auto:"))
            auto_failure = sum(1 for d in failure_store.load_all() if str(d.get("source_type", "")).startswith("auto:"))
            prevention_hits = 0
            estimated_tokens_saved_auto = sum(
                int(d.get("estimated_tokens_saved", 0))
                for d in success_store.load_all()
                if str(d.get("source_type", "")).startswith("auto:")
            )

        return {
            "success_patterns": success_count,
            "failure_patterns": failure_count,
            "project_rules": rule_count,
            "estimated_tokens_saved": total_saved,
            "auto_captured_success": auto_success,
            "auto_captured_failure": auto_failure,
            "prevention_hits": prevention_hits,
            "estimated_tokens_saved_auto": estimated_tokens_saved_auto,
            "days": days,
        }

    def observe_edit(self, payload: dict[str, Any]) -> dict[str, Any]:
        event = EditEvent(**payload)
        if not self.allowlist.is_allowed(event.project_path):
            return self._error("PROJECT_NOT_ALLOWED", event.project_path)

        if not self.settings.auto_capture_enabled:
            return {"event_id": event.event_id}

        event.agent_source = normalize_agent_source(event.agent_source)
        event.text_before = redact_secrets(event.text_before)
        event.text_after = redact_secrets(event.text_after)

        self._audit(
            actor=event.agent_source,
            action="observe.edit",
            target_type="edit_event",
            target_id=event.event_id,
            project_path=event.project_path,
            meta={
                "file_path": event.file_path,
                "language": event.language,
                "document_version": event.document_version,
                "text_before_len": len(event.text_before),
                "text_after_len": len(event.text_after),
            },
        )

        self._outcome_tracker.track_edit(event)
        return {"event_id": event.event_id}

    def observe_diagnostic(self, payload: dict[str, Any]) -> None:
        signal = DiagnosticSignal(**payload)
        self._audit(
            actor="observer",
            action="observe.diagnostic",
            target_type="diagnostic_signal",
            target_id=f"diag:{int(signal.timestamp)}",
            project_path=signal.project_path,
            meta={
                "file_path": signal.file_path,
                "severity": signal.severity,
                "is_new": signal.is_new,
                "is_resolved": signal.is_resolved,
            },
        )
        if not self.settings.auto_capture_enabled:
            return
        decisions = self._outcome_tracker.apply_diagnostic(signal)
        self._apply_outcome_decisions(decisions)

    def observe_test(self, payload: dict[str, Any]) -> None:
        signal = TestSignal(**payload)
        self._audit(
            actor="observer",
            action="observe.test",
            target_type="test_signal",
            target_id=f"test:{int(signal.timestamp)}",
            project_path=signal.project_path,
            meta={
                "test_name": signal.test_name,
                "file_path": signal.file_path,
                "status_before": signal.status_before,
                "status_after": signal.status_after,
            },
        )
        if not self.settings.auto_capture_enabled:
            return
        decisions = self._outcome_tracker.apply_test(signal)
        self._apply_outcome_decisions(decisions)

    def observe_revert(self, payload: dict[str, Any]) -> None:
        signal = RevertSignal(**payload)
        self._audit(
            actor="observer",
            action="observe.revert",
            target_type="revert_signal",
            target_id=signal.event_id,
            project_path=signal.project_path,
            meta={"timestamp": signal.timestamp},
        )
        if not self.settings.auto_capture_enabled:
            return
        decisions = self._outcome_tracker.apply_revert(signal)
        self._apply_outcome_decisions(decisions)

    def observe_terminal(self, payload: dict[str, Any]) -> None:
        signal = TerminalSignal(**payload)
        self._audit(
            actor="observer",
            action="observe.terminal",
            target_type="terminal_signal",
            target_id=f"terminal:{int(signal.ended_at)}",
            project_path=signal.project_path,
            meta={
                "cwd": signal.cwd,
                "exit_code": signal.exit_code,
            },
        )
        if not self.settings.auto_capture_enabled:
            return
        decisions = self._outcome_tracker.apply_terminal(signal)
        self._apply_outcome_decisions(decisions)

    def pre_edit_check(
        self,
        project_path: str,
        file_path: str,
        language: str,
        proposed_text: str,
        task_intent: str | None = None,
    ) -> dict[str, Any]:
        if not self.allowlist.is_allowed(project_path):
            return self._error("PROJECT_NOT_ALLOWED", project_path)

        now_ts = time.time()
        calls = self._pre_edit_check_calls[project_path]
        while calls and (now_ts - calls[0]) > 60:
            calls.popleft()

        if len(calls) >= self.settings.pre_edit_check_rate_limit_per_min:
            return self._error("RATE_LIMITED", project_path)

        calls.append(now_ts)
        result = self.prevention.pre_edit_check(
            project_path=project_path,
            file_path=file_path,
            language=language,
            proposed_text=proposed_text,
            task_intent=task_intent,
        )

        if result.get("matches") and self.conn is not None:
            UsageRepository(self.conn).create(
                event_id=str(uuid.uuid4()),
                memory_type="prevention_hit",
                memory_id=result["matches"][0]["failure_id"],
                query_text=(task_intent or proposed_text)[:500],
                tokens_saved=int(result.get("estimated_tokens_saved", 0)),
            )

        return result

    def get_pending_review(self) -> list[dict[str, Any]]:
        if (
            self.conn is None
            or self.capture.pattern_repo is None
            or self.capture.failure_repo is None
            or self.capture.rule_repo is None
        ):
            return []

        pending: list[dict[str, Any]] = []
        for item in self.capture.failure_repo.list_pending_review(limit=200):
            pending.append(
                {
                    "memory_type": "failure_pattern",
                    "memory_id": item.failure_id,
                    "title": item.task_intent,
                    "summary": item.prevention_rule,
                    "confidence": float(getattr(item, "confidence", item.confidence_score)),
                    "occurrence_count": int(getattr(item, "occurrence_count", 1)),
                    "review_state": item.review_state,
                    "agent_source": item.agent_source or None,
                    "last_seen_at": item.last_seen_at,
                    "source_type": item.source_type,
                    "source_ref": item.source_ref,
                }
            )

        for item in self.capture.pattern_repo.list_pending_review(limit=200):
            pending.append(
                {
                    "memory_type": "success_pattern",
                    "memory_id": item.pattern_id,
                    "title": item.name,
                    "summary": item.reasoning_summary,
                    "confidence": float(getattr(item, "confidence", item.confidence_score)),
                    "occurrence_count": int(getattr(item, "occurrence_count", 1)),
                    "review_state": item.review_state,
                    "agent_source": item.agent_source or None,
                    "last_seen_at": item.last_seen_at,
                    "source_type": item.source_type,
                    "source_ref": item.source_ref,
                }
            )

        for item in self.capture.rule_repo.list_pending_review(limit=200):
            pending.append(
                {
                    "memory_type": "project_rule",
                    "memory_id": item.rule_id,
                    "title": item.rule_text[:120],
                    "summary": item.rule_text,
                    "confidence": float(item.harvest_meta.get("raw_confidence", 0.0)),
                    "occurrence_count": 1,
                    "review_state": item.review_state,
                    "agent_source": None,
                    "last_seen_at": item.updated_at,
                    "source_type": item.source_type,
                    "source_ref": item.source_ref,
                }
            )

        pending.sort(key=lambda item: item.get("last_seen_at") or "", reverse=True)
        return pending

    def confirm_review(
        self,
        memory_type: str,
        memory_id: str,
        edits: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if (
            self.conn is None
            or self.capture.pattern_repo is None
            or self.capture.failure_repo is None
            or self.capture.rule_repo is None
        ):
            return self._error("STORAGE_NOT_INITIALIZED")

        if memory_type == "failure_pattern":
            item = self.capture.failure_repo.get_by_id(memory_id)
            if item is None:
                return self._error("NOT_FOUND")
            if edits:
                for key, value in edits.items():
                    if hasattr(item, key):
                        setattr(item, key, value)
                item.updated_at = self._now()
                self.capture.failure_repo.update(item)
            self.capture.failure_repo.set_review_state(memory_id, "confirmed")
            return {"ok": True, "memory_id": memory_id, "memory_type": memory_type}

        if memory_type == "success_pattern":
            item = self.capture.pattern_repo.get_by_id(memory_id)
            if item is None:
                return self._error("NOT_FOUND")
            if edits:
                for key, value in edits.items():
                    if hasattr(item, key):
                        setattr(item, key, value)
                item.updated_at = self._now()
                self.capture.pattern_repo.update(item)
            self.capture.pattern_repo.set_review_state(memory_id, "confirmed")
            return {"ok": True, "memory_id": memory_id, "memory_type": memory_type}

        if memory_type == "project_rule":
            item = self.capture.rule_repo.get_by_id(memory_id)
            if item is None:
                return self._error("NOT_FOUND")
            if edits:
                for key, value in edits.items():
                    if hasattr(item, key):
                        setattr(item, key, value)
                item.updated_at = self._now()
                self.capture.rule_repo.update(item)
            self.capture.rule_repo.set_review_state(memory_id, "confirmed")
            return {"ok": True, "memory_id": memory_id, "memory_type": memory_type}

        return self._error("INVALID_MEMORY_TYPE")

    def discard_review(self, memory_type: str, memory_id: str) -> dict[str, Any]:
        if (
            self.conn is None
            or self.capture.pattern_repo is None
            or self.capture.failure_repo is None
            or self.capture.rule_repo is None
        ):
            return self._error("STORAGE_NOT_INITIALIZED")

        if memory_type == "failure_pattern":
            self.capture.failure_repo.set_review_state(memory_id, "discarded")
            return {"ok": True, "memory_id": memory_id, "memory_type": memory_type}

        if memory_type == "success_pattern":
            self.capture.pattern_repo.set_review_state(memory_id, "discarded")
            return {"ok": True, "memory_id": memory_id, "memory_type": memory_type}

        if memory_type == "project_rule":
            self.capture.rule_repo.set_review_state(memory_id, "discarded")
            return {"ok": True, "memory_id": memory_id, "memory_type": memory_type}

        return self._error("INVALID_MEMORY_TYPE")

    def get_current_context(self) -> dict[str, Any]:
        context_path = self.base_dir / "agent-context.md"
        if not context_path.exists():
            return {"context_markdown": "", "path": str(context_path)}
        return {
            "context_markdown": context_path.read_text(encoding="utf-8"),
            "path": str(context_path),
        }

    def _apply_outcome_decisions(self, decisions: list[Any]) -> None:
        for decision in decisions:
            tracked = decision.tracked
            source = normalize_agent_source(tracked.edit_event.agent_source)
            if not source.startswith("agent:"):
                continue
            self.auto_capture.on_outcome(
                tracked=tracked,
                kind=decision.kind,
                confidence=decision.confidence,
            )

    # ------------------------------------------------------------------
    # Phase 8: Pre-command check and auto-recall on error
    # ------------------------------------------------------------------

    def check_command(
        self,
        command: str,
        project_path: str | None = None,
    ) -> dict[str, Any]:
        """Search failure patterns for any that match the given shell *command*.

        Returns a lightweight preview (no full body) so callers can warn the
        user before they run the command.
        """
        if not command.strip():
            return {"command": command, "matches": [], "warning_count": 0}

        results = self.search.search(command)
        failures = [r for r in results if r.result_type == "failure"][:5]

        matches = []
        for r in failures:
            f = r.obj
            matches.append(
                {
                    "failure_id": r.memory_id,
                    "title": r.title,
                    "prevention_rule": getattr(f, "prevention_rule", ""),
                    "severity": getattr(f, "severity", "medium"),
                    "confidence_score": r.confidence_score,
                }
            )

        self._audit(
            actor="mcp",
            action="memory.check_command",
            target_type="command",
            target_id=redact_secrets(command)[:120],
            project_path=project_path,
            meta={"match_count": len(matches)},
        )

        return {
            "command": command,
            "matches": matches,
            "warning_count": len(matches),
        }

    def recall_on_error(
        self,
        error_output: str,
        project_path: str | None = None,
        command: str | None = None,
    ) -> dict[str, Any]:
        """Search memory for patterns that match a terminal error output.

        Combines *error_output* with the optional *command* as a single query
        so that both contextual clues are used.
        """
        query_parts = []
        if command:
            query_parts.append(command.strip())
        if error_output:
            # Use first 300 chars of error output as the search query
            query_parts.append(error_output.strip()[:300])
        query = " ".join(query_parts) or "error"

        results = self.search.search(query)
        failures = [r for r in results if r.result_type == "failure"][:8]
        rules = [r for r in results if r.result_type == "rule"][:3]

        type_map = {"failure": "failure_pattern", "rule": "project_rule"}
        out: list[dict[str, Any]] = []
        for r in failures + rules:
            item: dict[str, Any] = {
                "memory_type": type_map.get(r.result_type, r.result_type),
                "memory_id": r.memory_id,
                "title": r.title,
                "summary": r.summary,
                "why_matched": r.why_matched,
                "severity": r.severity,
                "confidence_score": r.confidence_score,
            }
            if r.result_type == "failure":
                f = r.obj
                item["prevention_rule"] = getattr(f, "prevention_rule", "")
                item["corrected_approach"] = getattr(f, "corrected_approach", "")
            out.append(item)

        self._audit(
            actor="mcp",
            action="memory.recall_on_error",
            target_type="error",
            target_id=redact_secrets(query)[:120],
            project_path=project_path,
            meta={"match_count": len(out), "command": command},
        )

        return {
            "query": query,
            "results": out,
            "total": len(out),
        }

    # ------------------------------------------------------------------
    # Phase 4: Pro Databank integration
    # ------------------------------------------------------------------

    def _get_pro_adapter(self):
        """Lazy-load the ProSyncAdapter using current settings."""
        from vibecode.integrations.pro_sync import ProSyncAdapter

        return ProSyncAdapter(
            endpoint=self.settings.pro_endpoint,
            token=self.settings.pro_token,
        )

    def pro_share(self, memory_type: str, memory_id: str) -> dict[str, Any]:
        """Share a local pattern to the Pro databank."""
        adapter = self._get_pro_adapter()
        if not adapter.is_configured():
            return self._error("PRO_NOT_CONFIGURED")

        if self.conn is None:
            return self._error("STORAGE_NOT_INITIALIZED")

        data: dict[str, Any] = {}
        if memory_type == "failure_pattern":
            row = self.conn.execute(
                "SELECT * FROM failure_patterns WHERE failure_id = ? AND is_active = 1", (memory_id,)
            ).fetchone()
            if row is None:
                return self._error("NOT_FOUND")
            data = {
                k: v for k, v in dict(row).items()
                if k not in ("is_active", "content_hash", "agent_source", "source_ref")
            }
        elif memory_type == "success_pattern":
            row = self.conn.execute(
                "SELECT * FROM success_patterns WHERE pattern_id = ? AND is_active = 1", (memory_id,)
            ).fetchone()
            if row is None:
                return self._error("NOT_FOUND")
            data = {
                k: v for k, v in dict(row).items()
                if k not in ("is_active", "content_hash", "agent_source", "source_ref")
            }
        else:
            return self._error("INVALID_MEMORY_TYPE")

        result = adapter.submit(memory_type=memory_type, data=data)
        if "error" in result:
            return {"error": "PRO_SUBMIT_FAILED", "message": result["error"]}
        return result

    def pro_retract(self, submission_id: str) -> dict[str, Any]:
        """Retract a previously shared pattern from the Pro databank."""
        adapter = self._get_pro_adapter()
        if not adapter.is_configured():
            return self._error("PRO_NOT_CONFIGURED")
        result = adapter.retract(submission_id)
        if "error" in result:
            return {"error": "PRO_RETRACT_FAILED", "message": result["error"]}
        return result

    def pro_status(self) -> dict[str, Any]:
        """Return Pro databank connection status."""
        adapter = self._get_pro_adapter()
        if not adapter.is_configured():
            return {
                "configured": False,
                "message": "Set VIBECODE_PRO_ENDPOINT and VIBECODE_PRO_TOKEN to enable.",
            }
        result = adapter.get_status()
        result["configured"] = True
        return result

    def pro_search(self, query: str, max_results: int = 10) -> dict[str, Any]:
        """Search the Pro databank for patterns matching *query*."""
        adapter = self._get_pro_adapter()
        if not adapter.is_configured():
            return self._error("PRO_NOT_CONFIGURED")
        return adapter.search(query=query, max_results=max_results)

    # ------------------------------------------------------------------
    # Phase 5: Extended token report with source buckets
    # ------------------------------------------------------------------

    def get_token_report_buckets(self, project_path: str | None = None, days: int = 30) -> dict[str, Any]:
        """Return token report broken down by source_type bucket.

        Buckets:
          local     — manually captured patterns (source_type = 'manual' or 'session-learning')
          harvested — patterns extracted by the harvester (source_type LIKE 'harvest:%')
          auto      — auto-captured patterns (source_type LIKE 'auto:%')
          pro_team  — patterns from the Pro team databank (source_type LIKE 'pro_team:%')
          pro_global — patterns from the Pro global databank (source_type LIKE 'pro_global:%')
        """
        base_report = self.get_token_report(project_path=project_path, days=days)

        if self.conn is None:
            buckets = {
                "local": 0, "harvested": 0, "auto": 0, "pro_team": 0, "pro_global": 0
            }
        else:
            def _count(table: str, id_col: str, pattern: str) -> int:
                row = self.conn.execute(  # type: ignore[union-attr]
                    f"SELECT COUNT(*) AS c FROM {table} WHERE is_active = 1 AND source_type LIKE ?",
                    (pattern,),
                ).fetchone()
                return int(row["c"]) if row else 0

            buckets = {
                "local": (
                    _count("success_patterns", "pattern_id", "manual")
                    + _count("failure_patterns", "failure_id", "manual")
                    + _count("success_patterns", "pattern_id", "session-learning")
                    + _count("failure_patterns", "failure_id", "session-learning")
                ),
                "harvested": (
                    _count("success_patterns", "pattern_id", "harvest:%")
                    + _count("failure_patterns", "failure_id", "harvest:%")
                    + _count("project_rules", "rule_id", "harvest:%")
                ),
                "auto": (
                    _count("success_patterns", "pattern_id", "auto:%")
                    + _count("failure_patterns", "failure_id", "auto:%")
                ),
                "pro_team": (
                    _count("success_patterns", "pattern_id", "pro_team:%")
                    + _count("failure_patterns", "failure_id", "pro_team:%")
                ),
                "pro_global": (
                    _count("success_patterns", "pattern_id", "pro_global:%")
                    + _count("failure_patterns", "failure_id", "pro_global:%")
                ),
            }

        base_report["source_buckets"] = buckets
        return base_report

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
            "RATE_LIMITED": (
                "Rate limit exceeded for pre-edit checks.",
                "Reduce call frequency or wait one minute.",
            ),
            "NOT_FOUND": (
                "Requested memory item was not found.",
                "Refresh pending review and retry.",
            ),
            "INVALID_MEMORY_TYPE": (
                "Unsupported memory type.",
                "Use success_pattern, failure_pattern, or project_rule.",
            ),
            "PRO_NOT_CONFIGURED": (
                "Pro databank not configured.",
                "Set VIBECODE_PRO_ENDPOINT and VIBECODE_PRO_TOKEN environment variables.",
            ),
        }
        msg, fix = messages.get(code, ("Unknown error.", ""))
        result: dict[str, Any] = {"error": code, "message": msg, "fix": fix}
        if project_path:
            result["project_path"] = project_path
        return result
