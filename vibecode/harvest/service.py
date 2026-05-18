from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from vibecode.core.security import ProjectAllowlist, redact_secrets
from vibecode.db.audit_log_repository import AuditLogRepository
from vibecode.db.sqlite_connection import get_connection
from vibecode.db.sqlite_schema import create_schema
from vibecode.harvest.confidence import score_candidate
from vibecode.harvest.dedupe import dedupe_candidates, dedupe_candidates_with_embeddings
from vibecode.harvest.extractors import (
    ADRExtractor,
    ChangelogFixExtractor,
    ClaudeMdExtractor,
    InlineCommentExtractor,
    LinterConfigExtractor,
    MarkdownRuleExtractor,
)
from vibecode.harvest.normalizer import CandidateMemory, normalize_text
from vibecode.harvest.walker import DEFAULT_INCLUDE_PATTERNS, DocSourceWalker
from vibecode.models import FailurePattern, ProjectRule, SuccessPattern
from vibecode.repositories.failure_repository import FailureRepository
from vibecode.repositories.pattern_repository import PatternRepository
from vibecode.repositories.rule_repository import RuleRepository
from vibecode.services.embedding_service import EmbeddingService


class KnowledgeHarvester:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = Path(base_dir or (Path.cwd() / ".vibecode"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.allowlist = ProjectAllowlist(self.base_dir)
        self.walker = DocSourceWalker()
        self.embedding_service = EmbeddingService()
        self.claude_extractor = ClaudeMdExtractor()
        self.adr_extractor = ADRExtractor()
        self.changelog_extractor = ChangelogFixExtractor()
        self.linter_extractor = LinterConfigExtractor()
        self.inline_comment_extractor = InlineCommentExtractor()
        self.markdown_extractor = MarkdownRuleExtractor()
        self.extractors = [
            self.claude_extractor,
            self.adr_extractor,
            self.changelog_extractor,
            self.linter_extractor,
            self.inline_comment_extractor,
            self.markdown_extractor,
        ]

    @staticmethod
    def default_sources() -> list[str]:
        return list(DEFAULT_INCLUDE_PATTERNS)

    def scan(
        self,
        project_path: str,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        max_files: int = 500,
        auto_confirm_threshold: float = 0.8,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        if not self.allowlist.is_allowed(project_path):
            return {
                "error": "PROJECT_NOT_ALLOWED",
                "message": f"Project path is not allowlisted: {project_path}",
                "fix": "Run 'vibecode project allow --path <project_path>' first.",
            }

        root = Path(project_path).resolve()
        files = self.walker.walk(root, include=include, exclude=exclude, max_files=max_files)

        candidates: list[CandidateMemory] = []
        for file_path in files:
            rel = file_path.relative_to(root).as_posix()
            extracted = self._extract_for_file(file_path, rel)
            modified = file_path.stat().st_mtime
            for candidate in extracted:
                score_candidate(candidate, modified)
            candidates.extend(extracted)

        unique_candidates, in_batch_duplicates = dedupe_candidates(candidates)
        unique_candidates, semantic_duplicates = dedupe_candidates_with_embeddings(
            unique_candidates,
            self.embedding_service,
        )

        if dry_run:
            auto_confirmed = sum(1 for c in unique_candidates if c.confidence >= auto_confirm_threshold)
            queued = len(unique_candidates) - auto_confirmed
            return {
                "scanned_files": len(files),
                "candidates": len(unique_candidates),
                "auto_confirmed": auto_confirmed,
                "queued_for_review": queued,
                "duplicates_skipped": in_batch_duplicates + semantic_duplicates,
                "report_id": "preview",
                "report_path": str((self.base_dir / "harvest_report.json").as_posix()),
                "candidate_items": [c.to_preview() for c in unique_candidates],
                "extractor_counts": self._count_by_extractor(unique_candidates),
            }

        report_id = f"harv_{uuid.uuid4().hex[:12]}"
        created = 0
        auto_confirmed = 0
        queued = 0
        db_duplicates = 0

        conn = get_connection(self.base_dir)
        try:
            create_schema(conn)
            pattern_repo = PatternRepository(conn)
            failure_repo = FailureRepository(conn)
            rule_repo = RuleRepository(conn)
            audit_repo = AuditLogRepository(conn)

            # Rule table currently has no content_hash column, so normalize text for dedupe.
            existing_rule_texts = {normalize_text(r.rule_text) for r in rule_repo.list_active()}

            for candidate in unique_candidates:
                candidate.review_state = "confirmed" if candidate.confidence >= auto_confirm_threshold else "pending"
                harvest_meta = {
                    "extractor": candidate.extractor,
                    "raw_confidence": candidate.confidence,
                }

                if candidate.memory_type == "project_rule":
                    normalized_rule = normalize_text(candidate.rule_text)
                    if normalized_rule in existing_rule_texts:
                        db_duplicates += 1
                        continue

                    rule = ProjectRule(
                        rule_id=str(uuid.uuid4()),
                        rule_text=redact_secrets(candidate.rule_text),
                        rule_type=candidate.rule_type,
                        severity=candidate.severity,
                        tags=candidate.tags,
                        source_type=candidate.source_type,
                        source_ref=candidate.source_ref,
                        harvest_meta=harvest_meta,
                        review_state=candidate.review_state,
                    )
                    rule_repo.create(rule)
                    existing_rule_texts.add(normalized_rule)
                    target_type = "project_rule"
                    target_id = rule.rule_id

                elif candidate.memory_type == "failure_pattern":
                    content_hash = candidate.content_hash()
                    existing = failure_repo.get_by_content_hash(content_hash)
                    if existing:
                        failure_repo.mark_seen(existing.failure_id, confidence=candidate.confidence)
                        db_duplicates += 1
                        continue

                    failure = FailurePattern(
                        failure_id=str(uuid.uuid4()),
                        task_intent=redact_secrets(candidate.task_intent or candidate.title),
                        bad_suggestion=redact_secrets(candidate.bad_suggestion),
                        failure_reason=redact_secrets(candidate.failure_reason),
                        corrected_approach=redact_secrets(candidate.corrected_approach),
                        prevention_rule=redact_secrets(candidate.prevention_rule),
                        language=candidate.language,
                        framework=candidate.framework,
                        severity=candidate.severity,
                        source_type=candidate.source_type,
                        source_ref=candidate.source_ref,
                        harvest_meta=harvest_meta,
                        review_state=candidate.review_state,
                        confidence=candidate.confidence,
                        content_hash=content_hash,
                        last_seen_at=self._now(),
                    )
                    failure_repo.create(failure)
                    target_type = "failure_pattern"
                    target_id = failure.failure_id

                else:
                    content_hash = candidate.content_hash()
                    existing = pattern_repo.get_by_content_hash(content_hash)
                    if existing:
                        pattern_repo.mark_seen(existing.pattern_id, confidence=candidate.confidence)
                        db_duplicates += 1
                        continue

                    success = SuccessPattern(
                        pattern_id=str(uuid.uuid4()),
                        name=redact_secrets(candidate.title),
                        intent_description=redact_secrets(candidate.title),
                        reasoning_summary=redact_secrets(candidate.reasoning_summary or candidate.title),
                        code_after=redact_secrets(candidate.code_after),
                        language=candidate.language,
                        framework=candidate.framework,
                        source_type=candidate.source_type,
                        source_ref=candidate.source_ref,
                        harvest_meta=harvest_meta,
                        review_state=candidate.review_state,
                        confidence=candidate.confidence,
                        content_hash=content_hash,
                        last_seen_at=self._now(),
                    )
                    pattern_repo.create(success)
                    target_type = "success_pattern"
                    target_id = success.pattern_id

                created += 1
                if candidate.review_state == "confirmed":
                    auto_confirmed += 1
                else:
                    queued += 1

                audit_repo.record(
                    actor="harvester",
                    action="harvest_write",
                    target_type=target_type,
                    target_id=target_id,
                    project_path=str(root),
                    meta={
                        "source_type": candidate.source_type,
                        "source_ref": candidate.source_ref,
                        "review_state": candidate.review_state,
                        "confidence": candidate.confidence,
                    },
                )
        finally:
            conn.close()

        result = {
            "scanned_files": len(files),
            "candidates": len(unique_candidates),
            "auto_confirmed": auto_confirmed,
            "queued_for_review": queued,
            "duplicates_skipped": in_batch_duplicates + semantic_duplicates + db_duplicates,
            "report_id": report_id,
            "report_path": str((self.base_dir / "harvest_report.json").as_posix()),
            "candidate_items": [c.to_preview() for c in unique_candidates],
            "extractor_counts": self._count_by_extractor(unique_candidates),
        }
        self._write_report(report_id, result)
        return result

    def read_report(self, report_id: str | None = None) -> dict[str, Any]:
        if report_id:
            report_path = self.base_dir / "harvest_reports" / f"{report_id}.json"
            if report_path.exists():
                return json.loads(report_path.read_text(encoding="utf-8"))
        latest = self.base_dir / "harvest_report.json"
        if not latest.exists():
            return {
                "report_id": "none",
                "report_path": str(latest.as_posix()),
                "scanned_files": 0,
                "candidates": 0,
                "auto_confirmed": 0,
                "queued_for_review": 0,
                "duplicates_skipped": 0,
                "candidate_items": [],
                "extractor_counts": {},
            }
        return json.loads(latest.read_text(encoding="utf-8"))

    def _extract_for_file(self, path: Path, rel_path: str) -> list[CandidateMemory]:
        if self.claude_extractor.matches(rel_path):
            return self.claude_extractor.extract(path, rel_path)

        extracted: list[CandidateMemory] = []
        for extractor in self.extractors:
            if extractor is self.claude_extractor:
                continue
            if extractor.matches(rel_path):
                extracted.extend(extractor.extract(path, rel_path))
        return extracted

    @staticmethod
    def _count_by_extractor(candidates: list[CandidateMemory]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for candidate in candidates:
            counts[candidate.extractor] = counts.get(candidate.extractor, 0) + 1
        return counts

    def _write_report(self, report_id: str, report: dict[str, Any]) -> None:
        enriched = {
            **report,
            "report_id": report_id,
            "generated_at": self._now(),
        }
        latest = self.base_dir / "harvest_report.json"
        latest.write_text(json.dumps(enriched, indent=2), encoding="utf-8")

        history_dir = self.base_dir / "harvest_reports"
        history_dir.mkdir(parents=True, exist_ok=True)
        history = history_dir / f"{report_id}.json"
        history.write_text(json.dumps(enriched, indent=2), encoding="utf-8")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
