from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import sqlite3
import typer

from vibecode.db.sqlite_connection import get_connection, get_db_path
from vibecode.db.sqlite_schema import create_schema
from vibecode.models import AgentProfile
from vibecode.services.capture_service import CaptureService
from vibecode.services.export_service import ExportService
from vibecode.services.injection_service import InjectionService
from vibecode.services.migration_service import MigrationService
from vibecode.services.search_service import SearchResult, SearchService
from vibecode.services.token_service import TokenService
from vibecode.storage.json_store import JsonStore

app = typer.Typer(name="vibecode", help="VibeCode — Local AI Coding Memory")
postgres_app = typer.Typer(name="postgres", help="PostgreSQL backend commands")
service_app = typer.Typer(name="service", help="Local HTTP service commands")
mcp_app = typer.Typer(name="mcp", help="MCP server commands")
project_app = typer.Typer(name="project", help="Project allowlist commands")

app.add_typer(postgres_app)
app.add_typer(service_app)
app.add_typer(mcp_app)
app.add_typer(project_app)


def get_base_dir() -> Path:
    return Path.cwd() / ".vibecode"


def get_conn(base_dir: Path | None = None) -> sqlite3.Connection | None:
    db_path = get_db_path(base_dir)
    if db_path.exists():
        return get_connection(base_dir)
    return None


def _get_storage_backend(storage: str | None) -> str:
    if storage:
        return storage
    return "auto"


# ---------------------------------------------------------------------------
# JSON / SQLite commands (Packet 1 + 1B)
# ---------------------------------------------------------------------------

@app.command()
def init() -> None:
    base = get_base_dir()
    dirs = [
        base / "success_patterns",
        base / "failure_patterns",
        base / "project_rules",
        base / "agent_profiles",
        base / "token_reports",
        base / "exports",
    ]
    created_any = False
    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            typer.echo(f"Created: {d}")
            created_any = True
        else:
            typer.echo(f"Exists:  {d}")

    config_path = base / "config.json"
    if not config_path.exists():
        config_path.write_text('{"version": "0.1.0"}', encoding="utf-8")
        typer.echo(f"Created: {config_path}")
        created_any = True
    else:
        typer.echo(f"Exists:  {config_path}")

    capture = CaptureService(base)
    capture.seed_profiles()
    typer.echo("Seeded default agent profiles.")

    if created_any:
        typer.echo("VibeCode initialized.")
    else:
        typer.echo("VibeCode already initialized.")


@app.command()
def init_db() -> None:
    base = get_base_dir()
    conn = get_connection(base)
    create_schema(conn)
    conn.close()
    # Seed profiles into SQLite if empty
    capture = CaptureService(base, get_connection(base))
    capture.seed_profiles()
    capture.conn.close()
    typer.echo(f"SQLite database initialized: {get_db_path(base)}")


@app.command()
def db_status() -> None:
    base = get_base_dir()
    db_path = get_db_path(base)
    if not db_path.exists():
        typer.echo("SQLite database not found. Run: vibecode init-db")
        raise typer.Exit(1)
    conn = get_connection(base)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row["name"] for row in cursor.fetchall()]
    conn.close()
    typer.echo(f"Database: {db_path}")
    for t in tables:
        typer.echo(f"  Table: {t}")


@app.command()
def migrate_json_to_sqlite() -> None:
    base = get_base_dir()
    if not base.exists():
        typer.echo("Run 'vibecode init' first.")
        raise typer.Exit(1)
    db_path = get_db_path(base)
    if not db_path.exists():
        typer.echo("Run 'vibecode init-db' first.")
        raise typer.Exit(1)

    service = MigrationService(base)
    counts = service.migrate()
    typer.echo("Migration complete:")
    typer.echo(f"- success patterns imported: {counts['success_patterns']}")
    typer.echo(f"- failure patterns imported: {counts['failure_patterns']}")
    typer.echo(f"- project rules imported: {counts['project_rules']}")
    typer.echo(f"- agent profiles imported: {counts['agent_profiles']}")
    typer.echo(f"- duplicates skipped: {counts['duplicates_skipped']}")
    typer.echo(f"- errors: {counts['errors']}")


@app.command()
def status() -> None:
    base = get_base_dir()
    if not base.exists():
        typer.echo("VibeCode not initialized. Run: vibecode init")
        raise typer.Exit(1)

    conn = get_conn(base)
    if conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        for row in cursor.fetchall():
            typer.echo(f"Table: {row['name']}")
        conn.close()
    else:
        stores = {
            "Success patterns": JsonStore(base / "success_patterns"),
            "Failure patterns": JsonStore(base / "failure_patterns"),
            "Project rules": JsonStore(base / "project_rules"),
            "Agent profiles": JsonStore(base / "agent_profiles"),
        }
        for label, store in stores.items():
            typer.echo(f"{label}: {store.count()}")


# ---------------------------------------------------------------------------
# Capture commands (multi-backend)
# ---------------------------------------------------------------------------

@app.command()
def capture_success(
    name: str = typer.Option(None, "--name"),
    intent: str = typer.Option(None, "--intent"),
    language: str = typer.Option(None, "--language"),
    framework: str = typer.Option(None, "--framework"),
    tags: str = typer.Option(None, "--tags"),
    files: str = typer.Option(None, "--files"),
    summary: str = typer.Option(None, "--summary"),
    source_type: str = typer.Option(None, "--source-type"),
    source_ref: str = typer.Option(None, "--source-ref"),
    storage: str = typer.Option(None, "--storage"),
) -> None:
    base = get_base_dir()
    if not base.exists():
        typer.echo("Run 'vibecode init' first.")
        raise typer.Exit(1)

    _handle_capture_success(base, storage, name, intent, language, framework, tags, files, summary, source_type, source_ref)


def _handle_capture_success(
    base: Path,
    storage: str | None,
    name: str | None,
    intent: str | None,
    language: str | None,
    framework: str | None,
    tags: str | None,
    files: str | None,
    summary: str | None,
    source_type: str | None,
    source_ref: str | None,
) -> None:
    data: dict[str, Any] = {}
    data["name"] = _prompt(name, "Name")
    data["intent_description"] = _prompt(intent, "Intent")
    data["language"] = _prompt(language, "Language", "")
    data["framework"] = _prompt(framework, "Framework", "")
    data["tags"] = _prompt(tags, "Tags (comma-separated)", "")
    data["affected_files"] = _prompt(files, "Affected files (comma-separated)", "")
    data["reasoning_summary"] = _prompt(summary, "Reasoning summary")
    data["original_prompt"] = _prompt(None, "Original prompt", "")
    data["code_after"] = _prompt(None, "Code after (optional)", "")
    data["token_cost_original"] = int(_prompt(None, "Original token estimate", "0") or 0)
    data["token_cost_retrieval"] = int(_prompt(None, "Retrieval token estimate", "0") or 0)
    data["source_type"] = _prompt(source_type, "Source type", "manual")
    data["source_ref"] = _prompt(source_ref, "Source reference", "")

    if storage == "postgres":
        from vibecode.db.postgres_connection import get_db_session
        from vibecode.db.repositories import PostgresPatternRepository
        from vibecode.services.hash_service import HashService
        from vibecode.services.token_service import TokenService

        session = get_db_session()
        repo = PostgresPatternRepository(session)
        import uuid
        from datetime import datetime, timezone
        pattern = SuccessPattern(**data)
        pattern.pattern_id = str(uuid.uuid4())
        pattern.created_at = datetime.now(timezone.utc).isoformat()
        pattern.updated_at = pattern.created_at
        pattern.content_hash = HashService.hash_success_pattern(pattern)
        existing = repo.get_by_content_hash(pattern.content_hash)
        if existing:
            typer.echo(f"Duplicate detected. Existing ID: {existing.pattern_id}")
            session.close()
            return
        original = pattern.token_cost_original or TokenService.estimate_tokens(
            pattern.original_prompt + pattern.reasoning_summary
        )
        retrieval = pattern.token_cost_retrieval or TokenService.estimate_tokens(
            pattern.reasoning_summary
        )
        pattern.token_cost_original = original
        pattern.token_cost_retrieval = retrieval
        pattern.estimated_tokens_saved = TokenService.estimate_tokens_saved(original, retrieval)
        repo.create(pattern)
        typer.echo(f"Captured success pattern: {pattern.pattern_id}")
        session.close()
    else:
        conn = get_conn(base)
        capture = CaptureService(base, conn)
        pattern, created = capture.capture_success(data)
        if conn:
            conn.close()
        if created:
            typer.echo(f"Captured success pattern: {pattern.pattern_id}")
        else:
            typer.echo(f"Duplicate detected. Existing ID: {pattern.pattern_id}")


@app.command()
def capture_failure(
    task_intent: str = typer.Option(None, "--task-intent"),
    bad_suggestion: str = typer.Option(None, "--bad-suggestion"),
    failure_reason: str = typer.Option(None, "--failure-reason"),
    corrected_approach: str = typer.Option(None, "--corrected-approach"),
    prevention_rule: str = typer.Option(None, "--prevention-rule"),
    severity: str = typer.Option(None, "--severity"),
    language: str = typer.Option(None, "--language"),
    framework: str = typer.Option(None, "--framework"),
    tags: str = typer.Option(None, "--tags"),
    files: str = typer.Option(None, "--files"),
    source_type: str = typer.Option(None, "--source-type"),
    source_ref: str = typer.Option(None, "--source-ref"),
    storage: str = typer.Option(None, "--storage"),
) -> None:
    base = get_base_dir()
    if not base.exists():
        typer.echo("Run 'vibecode init' first.")
        raise typer.Exit(1)

    data: dict[str, Any] = {}
    data["task_intent"] = _prompt(task_intent, "Task intent")
    data["bad_suggestion"] = _prompt(bad_suggestion, "Bad suggestion")
    data["failure_reason"] = _prompt(failure_reason, "Why it failed")
    data["corrected_approach"] = _prompt(corrected_approach, "Corrected approach", "")
    data["prevention_rule"] = _prompt(prevention_rule, "Prevention rule")
    data["severity"] = _prompt(severity, "Severity (low/medium/high/critical)")
    data["language"] = _prompt(language, "Language", "")
    data["framework"] = _prompt(framework, "Framework", "")
    data["tags"] = _prompt(tags, "Tags (comma-separated)", "")
    data["affected_files"] = _prompt(files, "Affected files (comma-separated)", "")
    data["source_type"] = _prompt(source_type, "Source type", "manual")
    data["source_ref"] = _prompt(source_ref, "Source reference", "")

    if storage == "postgres":
        from vibecode.db.postgres_connection import get_db_session
        from vibecode.db.repositories import PostgresFailureRepository
        from vibecode.services.hash_service import HashService

        session = get_db_session()
        repo = PostgresFailureRepository(session)
        import uuid
        from datetime import datetime, timezone
        pattern = FailurePattern(**data)
        pattern.failure_id = str(uuid.uuid4())
        pattern.created_at = datetime.now(timezone.utc).isoformat()
        pattern.updated_at = pattern.created_at
        pattern.content_hash = HashService.hash_failure_pattern(pattern)
        existing = repo.get_by_content_hash(pattern.content_hash)
        if existing:
            typer.echo(f"Duplicate detected. Existing ID: {existing.failure_id}")
            session.close()
            return
        repo.create(pattern)
        typer.echo(f"Captured failure pattern: {pattern.failure_id}")
        session.close()
    else:
        conn = get_conn(base)
        capture = CaptureService(base, conn)
        pattern, created = capture.capture_failure(data)
        if conn:
            conn.close()
        if created:
            typer.echo(f"Captured failure pattern: {pattern.failure_id}")
        else:
            typer.echo(f"Duplicate detected. Existing ID: {pattern.failure_id}")


@app.command()
def add_rule(
    rule_text: str = typer.Option(None, "--rule-text"),
    rule_type: str = typer.Option(None, "--rule-type"),
    severity: str = typer.Option(None, "--severity"),
    tags: str = typer.Option(None, "--tags"),
    source_success_pattern_id: str = typer.Option(None, "--source-success-id"),
    source_failure_id: str = typer.Option(None, "--source-failure-id"),
    storage: str = typer.Option(None, "--storage"),
) -> None:
    base = get_base_dir()
    if not base.exists():
        typer.echo("Run 'vibecode init' first.")
        raise typer.Exit(1)

    data: dict[str, Any] = {}
    data["rule_text"] = _prompt(rule_text, "Rule text")
    data["rule_type"] = _prompt(rule_type, "Rule type")
    data["severity"] = _prompt(severity, "Severity (low/medium/high/critical)")
    data["tags"] = _prompt(tags, "Tags (comma-separated)", "")
    data["source_success_pattern_id"] = _prompt(
        source_success_pattern_id, "Source success pattern ID", ""
    )
    data["source_failure_id"] = _prompt(
        source_failure_id, "Source failure ID", ""
    )

    if storage == "postgres":
        from vibecode.db.postgres_connection import get_db_session
        from vibecode.db.repositories import PostgresProjectRuleRepository

        session = get_db_session()
        repo = PostgresProjectRuleRepository(session)
        import uuid
        from datetime import datetime, timezone
        rule = ProjectRule(**data)
        rule.rule_id = str(uuid.uuid4())
        rule.created_at = datetime.now(timezone.utc).isoformat()
        rule.updated_at = rule.created_at
        repo.create(rule)
        typer.echo(f"Added project rule: {rule.rule_id}")
        session.close()
    else:
        conn = get_conn(base)
        capture = CaptureService(base, conn)
        rule = capture.add_rule(data)
        if conn:
            conn.close()
        typer.echo(f"Added project rule: {rule.rule_id}")


# ---------------------------------------------------------------------------
# Search / Inject / Report / Export (multi-backend)
# ---------------------------------------------------------------------------

@app.command()
def search(
    query: str,
    storage: str = typer.Option(None, "--storage"),
) -> None:
    base = get_base_dir()
    if not base.exists():
        typer.echo("Run 'vibecode init' first.")
        raise typer.Exit(1)

    if storage == "postgres":
        from vibecode.db.postgres_connection import get_db_session
        from vibecode.services.postgres_search_service import PostgresSearchService

        session = get_db_session()
        service = PostgresSearchService(session)
        results = service.search(query)
        session.close()
    else:
        conn = get_conn(base)
        service = SearchService(base, conn)
        results = service.search(query)
        if conn:
            conn.close()

    if not results:
        typer.echo("No results found.")
        return

    for r in results:
        if r.result_type == "failure":
            obj = r.obj
            typer.echo(f"[FAILURE] {obj.prevention_rule}")
            typer.echo(f"Why matched: {', '.join(r.matched_terms)}")
            typer.echo(f"Severity: {obj.severity}")
        elif r.result_type == "rule":
            obj = r.obj
            typer.echo(f"[RULE] {obj.rule_text}")
            typer.echo(f"Why matched: {', '.join(r.matched_terms)}")
        elif r.result_type == "success":
            obj = r.obj
            typer.echo(f"[SUCCESS] {obj.name}")
            typer.echo(f"Why matched: {', '.join(r.matched_terms)}")
        typer.echo("")


@app.command()
def inject(
    query: str = typer.Option(..., "--query"),
    profile: str = typer.Option(..., "--profile"),
    storage: str = typer.Option(None, "--storage"),
) -> None:
    base = get_base_dir()
    if not base.exists():
        typer.echo("Run 'vibecode init' first.")
        raise typer.Exit(1)

    if storage == "postgres":
        from vibecode.db.postgres_connection import get_db_session
        from vibecode.db.repositories import PostgresAgentProfileRepository
        from vibecode.services.injection_service import InjectionService
        from vibecode.services.postgres_search_service import PostgresSearchService
        from vibecode.services.token_service import TokenService

        session = get_db_session()
        profile_repo = PostgresAgentProfileRepository(session)
        profile_obj = profile_repo.get_by_name(profile)
        if profile_obj is None:
            session.close()
            typer.echo(f"Profile not found: {profile}")
            raise typer.Exit(1)

        search_service = PostgresSearchService(session)
        token_service = TokenService()

        results = search_service.search(query)
        md = _build_inject_markdown(query, profile_obj, results, token_service)
        session.close()
        typer.echo(md)
    else:
        conn = get_conn(base)
        capture = CaptureService(base, conn)
        profile_obj = capture.get_profile_by_name(profile)
        if profile_obj is None:
            if conn:
                conn.close()
            typer.echo(f"Profile not found: {profile}")
            raise typer.Exit(1)

        service = InjectionService(base, conn)
        markdown = service.inject(query, profile_obj)
        if conn:
            conn.close()
        typer.echo(markdown)


def _build_inject_markdown(
    query: str,
    profile: AgentProfile,
    results: list[SearchResult],
    token_service: TokenService,
) -> str:
    from vibecode.models import FailurePattern, ProjectRule, SuccessPattern

    failures = [r for r in results if r.result_type == "failure"]
    rules = [r for r in results if r.result_type == "rule"]
    successes = [r for r in results if r.result_type == "success"]

    lines: list[str] = [
        "# VibeCode Agent Context",
        "",
        f"## Task Query",
        query,
        "",
    ]

    budget = profile.max_context_tokens
    current_tokens = token_service.estimate_tokens("\n".join(lines))

    def fmt_failures(items: list[SearchResult]) -> str:
        out: list[str] = []
        for r in items:
            f = r.obj
            assert isinstance(f, FailurePattern)
            out.append(f"- **[{f.severity.upper()}]** {f.prevention_rule}")
            out.append(f"  - *Why:* {f.failure_reason}")
            if f.corrected_approach:
                out.append(f"  - *Corrected approach:* {f.corrected_approach}")
        return "\n".join(out)

    def fmt_rules(items: list[SearchResult]) -> str:
        out: list[str] = []
        for r in items:
            rule = r.obj
            assert isinstance(rule, ProjectRule)
            out.append(f"- **[{rule.severity.upper()}]** {rule.rule_text}")
            out.append(f"  - Type: {rule.rule_type}")
        return "\n".join(out)

    def fmt_successes(items: list[SearchResult]) -> str:
        out: list[str] = []
        for r in items:
            s = r.obj
            assert isinstance(s, SuccessPattern)
            out.append(f"- **{s.name}**")
            out.append(f"  - *Intent:* {s.intent_description}")
            out.append(f"  - *Summary:* {s.reasoning_summary}")
            if s.estimated_tokens_saved:
                out.append(f"  - *Tokens saved:* ~{s.estimated_tokens_saved}")
        return "\n".join(out)

    sections: list[tuple[str, str, int]] = []
    if profile.include_failure_patterns and failures:
        critical_high = [f for f in failures if f.severity in ("critical", "high")]
        if critical_high:
            sections.append(("Relevant Failure Warnings", fmt_failures(critical_high), 0))
        other = [f for f in failures if f.severity not in ("critical", "high")]
        if other:
            sections.append(("Relevant Failure Warnings", fmt_failures(other), 1))
    if profile.include_project_rules and rules:
        sections.append(("Relevant Project Rules", fmt_rules(rules), 2))
    if profile.include_success_patterns and successes:
        sections.append(("Relevant Success Patterns", fmt_successes(successes), 3))

    sections.sort(key=lambda s: s[2])
    for name, content, _ in sections:
        section_tokens = token_service.estimate_tokens(content)
        if current_tokens + section_tokens <= budget:
            lines.append(f"## {name}")
            lines.append("")
            lines.append(content)
            lines.append("")
            current_tokens += section_tokens
        elif name in ("Relevant Failure Warnings", "Relevant Project Rules"):
            trimmed = _trim_content(content, budget - current_tokens, token_service)
            if trimmed:
                lines.append(f"## {name}")
                lines.append("")
                lines.append(trimmed)
                lines.append("")
                current_tokens += token_service.estimate_tokens(trimmed)

    lines.append("## Token Budget")
    lines.append(f"- Profile limit: {profile.max_context_tokens} tokens")
    lines.append(f"- Estimated context used: {current_tokens} tokens")
    lines.append("")
    lines.append("## Instructions To Agent")
    lines.append(
        "Apply the above project rules and failure warnings before proposing code. "
        "Reuse the success patterns where applicable."
    )
    lines.append("")
    return "\n".join(lines)


def _trim_content(content: str, max_tokens: int, token_service: TokenService) -> str:
    lines = content.splitlines()
    trimmed: list[str] = []
    current = 0
    for line in lines:
        line_tokens = token_service.estimate_tokens(line)
        if current + line_tokens > max_tokens:
            break
        trimmed.append(line)
        current += line_tokens
    return "\n".join(trimmed)


@app.command()
def report(
    storage: str = typer.Option(None, "--storage"),
) -> None:
    base = get_base_dir()
    if not base.exists():
        typer.echo("Run 'vibecode init' first.")
        raise typer.Exit(1)

    if storage == "postgres":
        from vibecode.db.postgres_connection import get_db_session
        from sqlalchemy import func

        session = get_db_session()
        from vibecode.db.models import SuccessPattern, FailurePattern, ProjectRule

        success_count = session.query(SuccessPattern).filter(SuccessPattern.is_active.is_(True)).count()
        failure_count = session.query(FailurePattern).filter(FailurePattern.is_active.is_(True)).count()
        rule_count = session.query(ProjectRule).filter(ProjectRule.is_active.is_(True)).count()
        total_saved = (
            session.query(func.coalesce(func.sum(SuccessPattern.estimated_tokens_saved), 0))
            .filter(SuccessPattern.is_active.is_(True))
            .scalar()
        )
        most_used = (
            session.query(SuccessPattern.name, SuccessPattern.usage_count)
            .filter(SuccessPattern.is_active.is_(True), SuccessPattern.usage_count > 0)
            .order_by(SuccessPattern.usage_count.desc())
            .limit(5)
            .all()
        )
        highest_severity = (
            session.query(FailurePattern.severity, FailurePattern.task_intent)
            .filter(FailurePattern.severity.in_(["critical", "high"]))
            .limit(5)
            .all()
        )
        session.close()
    else:
        conn = get_conn(base)
        if conn:
            cursor = conn.execute("SELECT COUNT(*) AS c FROM success_patterns WHERE is_active = 1")
            success_count = cursor.fetchone()["c"]
            cursor = conn.execute("SELECT COUNT(*) AS c FROM failure_patterns WHERE is_active = 1")
            failure_count = cursor.fetchone()["c"]
            cursor = conn.execute("SELECT COUNT(*) AS c FROM project_rules WHERE is_active = 1")
            rule_count = cursor.fetchone()["c"]
            cursor = conn.execute(
                "SELECT COALESCE(SUM(estimated_tokens_saved), 0) AS total FROM success_patterns WHERE is_active = 1"
            )
            total_saved = cursor.fetchone()["total"]
            cursor = conn.execute(
                "SELECT name, usage_count FROM success_patterns WHERE is_active = 1 AND usage_count > 0 ORDER BY usage_count DESC LIMIT 5"
            )
            most_used = [(r["name"], r["usage_count"]) for r in cursor.fetchall()]
            cursor = conn.execute(
                "SELECT severity, task_intent FROM failure_patterns WHERE severity IN ('critical', 'high') LIMIT 5"
            )
            highest_severity = [(r["severity"], r["task_intent"]) for r in cursor.fetchall()]
            conn.close()
        else:
            success_store = JsonStore(base / "success_patterns")
            failure_store = JsonStore(base / "failure_patterns")
            rule_store = JsonStore(base / "project_rules")
            success_count = success_store.count()
            failure_count = failure_store.count()
            rule_count = rule_store.count()
            total_saved = 0
            most_used = []
            for data in success_store.load_all():
                total_saved += data.get("estimated_tokens_saved", 0)
                usage = data.get("usage_count", 0)
                if usage > 0:
                    most_used.append((data.get("name", "Unknown"), usage))
            highest_severity = []
            for data in failure_store.load_all():
                if data.get("severity") in ("critical", "high"):
                    highest_severity.append((data.get("severity", ""), data.get("task_intent", "Unknown")))

    typer.echo(f"Total success patterns: {success_count}")
    typer.echo(f"Total failure patterns: {failure_count}")
    typer.echo(f"Total project rules: {rule_count}")
    typer.echo(f"Estimated total tokens saved: {total_saved}")

    if most_used:
        typer.echo("Most used patterns:")
        for name, usage in most_used[:5]:
            typer.echo(f"  - {name} ({usage} uses)")
    else:
        typer.echo("Most used patterns: none yet")

    if highest_severity:
        typer.echo("Highest severity failures:")
        for sev, intent in highest_severity[:5]:
            typer.echo(f"  - [{sev.upper()}] {intent}")
    else:
        typer.echo("Highest severity failures: none")


@app.command()
def export_memory(
    storage: str = typer.Option(None, "--storage"),
) -> None:
    base = get_base_dir()
    if not base.exists():
        typer.echo("Run 'vibecode init' first.")
        raise typer.Exit(1)

    conn = get_conn(base)
    service = ExportService(base, conn)
    paths = service.export_all()
    if conn:
        conn.close()
    for p in paths:
        typer.echo(f"Exported: {p}")


# ---------------------------------------------------------------------------
# PostgreSQL subcommands
# ---------------------------------------------------------------------------

@postgres_app.command("init")
def postgres_init() -> None:
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    typer.echo("PostgreSQL schema initialized via Alembic.")


@postgres_app.command("status")
def postgres_status() -> None:
    from vibecode.db.postgres_connection import get_db_session

    session = get_db_session()
    from sqlalchemy import inspect

    inspector = inspect(session.bind)
    tables = inspector.get_table_names()
    session.close()
    typer.echo("PostgreSQL tables:")
    for t in tables:
        typer.echo(f"  {t}")


@postgres_app.command("migrate")
def postgres_migrate() -> None:
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    typer.echo("PostgreSQL migrations applied.")


@app.command()
def migrate_sqlite_to_postgres() -> None:
    base = get_base_dir()
    db_path = get_db_path(base)
    if not db_path.exists():
        typer.echo("SQLite database not found.")
        raise typer.Exit(1)

    from vibecode.db.postgres_connection import get_db_session
    from vibecode.services.sqlite_to_postgres_migration_service import (
        SqliteToPostgresMigrationService,
    )

    session = get_db_session()
    service = SqliteToPostgresMigrationService(db_path, session)
    counts = service.migrate()
    session.close()
    typer.echo("Migration complete:")
    typer.echo(f"- users created: {counts['users']}")
    typer.echo(f"- projects created: {counts['projects']}")
    typer.echo(f"- success patterns imported: {counts['success_patterns']}")
    typer.echo(f"- failure patterns imported: {counts['failure_patterns']}")
    typer.echo(f"- project rules imported: {counts['project_rules']}")
    typer.echo(f"- agent profiles imported: {counts['agent_profiles']}")
    typer.echo(f"- usage events imported: {counts['usage_events']}")
    typer.echo(f"- duplicates skipped: {counts['duplicates_skipped']}")
    typer.echo(f"- errors: {counts['errors']}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Service commands
# ---------------------------------------------------------------------------

@service_app.command("start")
def service_start(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8765, "--port"),
) -> None:
    import uvicorn
    from vibecode.api.app import create_app

    typer.echo(f"Starting VibeCode service on {host}:{port}")
    uvicorn.run(create_app(), host=host, port=port, log_level="info")


@service_app.command("status")
def service_status() -> None:
    from vibecode.core.memory_service import VibeCodeService

    svc = VibeCodeService()
    health = svc.health_check()
    for k, v in health.items():
        typer.echo(f"{k}: {v}")


@service_app.command("stop")
def service_stop() -> None:
    typer.echo("Service stop is best-effort. Use Ctrl+C if running in foreground.")


@service_app.command("doctor")
def service_doctor() -> None:
    base = get_base_dir()
    checks = {
        ".vibecode exists": base.exists(),
        "config.json exists": (base / "config.json").exists(),
        "success_patterns dir": (base / "success_patterns").exists(),
        "failure_patterns dir": (base / "failure_patterns").exists(),
        "project_rules dir": (base / "project_rules").exists(),
        "agent_profiles dir": (base / "agent_profiles").exists(),
        "SQLite DB": get_db_path(base).exists(),
    }
    all_ok = True
    for label, ok in checks.items():
        status = "OK" if ok else "MISSING"
        typer.echo(f"  [{status}] {label}")
        if not ok:
            all_ok = False
    if all_ok:
        typer.echo("All checks passed.")
    else:
        typer.echo("Some checks failed. Run 'vibecode init' and 'vibecode init-db'.")


# ---------------------------------------------------------------------------
# MCP commands
# ---------------------------------------------------------------------------

@mcp_app.command("start")
def mcp_start() -> None:
    from vibecode.mcp.server import run_mcp_server

    typer.echo("Starting VibeCode MCP server (stdio)...")
    import asyncio
    asyncio.run(run_mcp_server())


@mcp_app.command("doctor")
def mcp_doctor() -> None:
    try:
        from mcp.server.fastmcp import FastMCP
        typer.echo("MCP SDK: OK")
    except ImportError:
        typer.echo("MCP SDK: NOT INSTALLED")
        raise typer.Exit(1)
    try:
        from vibecode.mcp.server import mcp
        tools = [t.name for t in mcp._tool_manager._tools.values()]
        typer.echo(f"MCP tools registered: {len(tools)}")
        for t in tools:
            typer.echo(f"  - {t}")
    except Exception as e:
        typer.echo(f"MCP tool load error: {e}")
        raise typer.Exit(1)


@mcp_app.command("write-cursor-config")
def mcp_write_cursor_config() -> None:
    from vibecode.integrations.cursor import write_cursor_config

    path = write_cursor_config()
    typer.echo(f"Cursor MCP config written: {path}")


@mcp_app.command("write-antigravity-config")
def mcp_write_antigravity_config() -> None:
    from vibecode.integrations.antigravity import write_agents_md

    path = write_agents_md()
    typer.echo(f"Antigravity AGENTS.md written: {path}")


# ---------------------------------------------------------------------------
# Project allowlist commands
# ---------------------------------------------------------------------------

@project_app.command("allow")
def project_allow(path: str) -> None:
    from vibecode.core.security import ProjectAllowlist

    allowlist = ProjectAllowlist(get_base_dir())
    allowlist.add(path)
    typer.echo(f"Added to allowlist: {path}")


@project_app.command("list")
def project_list() -> None:
    from vibecode.core.security import ProjectAllowlist

    allowlist = ProjectAllowlist(get_base_dir())
    projects = allowlist.list()
    if not projects:
        typer.echo("No projects in allowlist.")
        return
    for p in projects:
        typer.echo(f"  {p}")


@project_app.command("remove")
def project_remove(path: str) -> None:
    from vibecode.core.security import ProjectAllowlist

    allowlist = ProjectAllowlist(get_base_dir())
    allowlist.remove(path)
    typer.echo(f"Removed from allowlist: {path}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _prompt(value: str | None, text: str, default: str = "") -> str:
    if value is not None:
        return value
    return typer.prompt(text, default=default)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
