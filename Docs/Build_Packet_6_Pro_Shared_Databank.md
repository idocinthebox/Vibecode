# Build Packet 6: VibeCode Pro Shared Databank

## Senior Build Packet

Project: VibeCode - Token-Efficient AI Coding Memory Layer
Phase: 6 (Pro)
Purpose: Add an opt-in shared databank where Pro users can contribute anonymized patterns and retrieve high-quality community knowledge for all connected agents.
Target Builder: Codex (primary) / GPT-5.5 / Claude Opus / Claude Sonnet / Cursor Agent
Difficulty: Advanced
Estimated Build Time: 24-32 hours
Prerequisites: Packets 1, 1B, 2, 3A, 4A, 4B, 4C, 5 complete.

---

## 1. Executive Summary

Packet 6 introduces a Pro-only shared memory layer on top of local VibeCode memory.

Current behavior:
- Retrieval uses local success patterns, failure patterns, and project rules.
- Auto-capture is local only.

New behavior:
- Pro users can opt in to contribute sanitized patterns to a global or team-scoped databank.
- Retrieval can include shared results ranked with local-first priority.
- Moderation and quality scoring gate what becomes publicly retrievable.

Design constraint:
- Local memory remains primary.
- Shared databank is additive, optional, and privacy-safe.

---

## 2. Core Design Principles

1. Local-first retrieval never regresses.
2. Explicit opt-in for all uploads.
3. Privacy by default: redact, hash, minimize.
4. Community quality over raw volume.
5. Fully auditable moderation decisions.
6. Reversible publishing and takedown path.

---

## 3. Product Scope

### In Scope

- Pro auth and entitlement checks.
- Contribution pipeline (submit, dedupe, review, publish).
- Shared retrieval API with ranking.
- Feedback loop from user actions (accepted, rejected, edited).
- Moderation queue with approve/reject/escalate.
- Team/private scopes for enterprise tier.

### Out of Scope (Packet 6)

- Billing implementation details.
- Full social layer (comments, following, leaderboards UI).
- Real-time collaboration editing.
- Automatic code application from shared results.

---

## 4. High-Level Architecture

~~~text
Local VSCode Extension
  -> Local VibeCode Service (existing)
     -> Pro Sync Adapter (new)
        -> Shared Databank API (new)
           -> Moderation + Quality Pipeline
           -> Databank Store (PostgreSQL + pgvector)
~~~

### Retrieval order

1. Local memory search
2. Team databank (if enabled)
3. Global databank
4. Merge + rerank + return top K

---

## 5. API Contracts

Base URL:
- https://api.vibecode.dev/v1

Auth:
- Authorization: Bearer <pro_access_token>
- X-VibeCode-Client-Version: <semver>
- X-VibeCode-Install-Id: <uuid>

Common response envelope:
~~~json
{
  "request_id": "req_01J...",
  "ok": true,
  "data": {}
}
~~~

Common error envelope:
~~~json
{
  "request_id": "req_01J...",
  "ok": false,
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests",
    "retry_after_sec": 30
  }
}
~~~

### 5.1 Submit contribution

Method and path:
- POST /databank/contributions

Request:
~~~json
{
  "submission_id": "subm_01J...",
  "scope": "global",
  "memory_type": "failure_pattern",
  "source": {
    "client_generated_at": "2026-05-17T14:20:00Z",
    "agent_source": "agent:GitHub.copilot",
    "vibecode_version": "0.3.0"
  },
  "content": {
    "title": "Avoid sync sqlite3 in async FastAPI route",
    "summary": "Using sqlite3.connect in async handlers blocks the event loop.",
    "prevention_rule": "Use async SQLAlchemy session or aiosqlite.",
    "corrected_approach": "async with aiosqlite.connect(db) as conn: ...",
    "language": "python",
    "framework": "fastapi",
    "error_fingerprint": "NameError|sqlite3.connect|async",
    "tags": ["async", "db", "performance"]
  },
  "metrics": {
    "local_confidence": 0.82,
    "occurrence_count": 4,
    "estimated_tokens_saved": 120
  },
  "privacy": {
    "redaction_version": "r1",
    "pii_risk_score": 0.04,
    "contains_raw_code": false,
    "content_hash": "sha256:..."
  }
}
~~~

Response:
~~~json
{
  "request_id": "req_...",
  "ok": true,
  "data": {
    "submission_id": "subm_01J...",
    "dedupe_status": "new",
    "moderation_state": "queued",
    "estimated_review_sla_min": 30
  }
}
~~~

Validation rules:
- memory_type in [success_pattern, failure_pattern, project_rule]
- scope in [global, team]
- pii_risk_score <= 0.25 or force moderation_state=quarantined
- title <= 140 chars
- summary <= 500 chars

### 5.2 Search shared databank

Method and path:
- POST /databank/search

Request:
~~~json
{
  "query": "async db access in fastapi endpoint",
  "scope": ["team", "global"],
  "language": "python",
  "framework": "fastapi",
  "memory_types": ["failure_pattern", "success_pattern"],
  "max_results": 10,
  "include_explanations": true,
  "context": {
    "task_intent": "Prevent blocking DB calls",
    "error_signals": ["event loop blocked"]
  }
}
~~~

Response:
~~~json
{
  "request_id": "req_...",
  "ok": true,
  "data": {
    "results": [
      {
        "result_id": "pat_01J...",
        "scope": "global",
        "memory_type": "failure_pattern",
        "title": "Avoid sync sqlite3 in async FastAPI route",
        "summary": "sqlite3.connect blocks async handlers",
        "prevention_rule": "Use async SQLAlchemy session or aiosqlite",
        "corrected_approach": "async with aiosqlite.connect(...)",
        "ranking_score": 0.89,
        "confidence": 0.91,
        "quality_score": 0.87,
        "trust_score": 0.78,
        "freshness_days": 12,
        "explanations": {
          "semantic_match": 0.93,
          "language_match": 1.0,
          "framework_match": 1.0,
          "accepted_recently": 0.71
        }
      }
    ],
    "retrieval_time_ms": 42
  }
}
~~~

### 5.3 Feedback on result quality

Method and path:
- POST /databank/feedback

Request:
~~~json
{
  "result_id": "pat_01J...",
  "action": "accepted",
  "context": {
    "task_intent": "Fix async db route",
    "agent": "agent:GitHub.copilot"
  },
  "outcome": {
    "resolved_issue": true,
    "edited_before_apply": false
  }
}
~~~

Response:
~~~json
{
  "request_id": "req_...",
  "ok": true,
  "data": {
    "recorded": true
  }
}
~~~

Action enum:
- accepted
- rejected
- edited_then_accepted
- reported_incorrect

### 5.4 Pull updates for local cache

Method and path:
- GET /databank/sync?since_cursor=<cursor>&limit=200

Response:
~~~json
{
  "request_id": "req_...",
  "ok": true,
  "data": {
    "cursor": "cur_01J...",
    "items": [
      {
        "event": "published",
        "pattern_id": "pat_01J...",
        "updated_at": "2026-05-17T14:30:00Z"
      }
    ]
  }
}
~~~

### 5.5 Moderation queue (moderator role)

Method and path:
- GET /moderation/queue?state=queued&limit=50

Response:
~~~json
{
  "request_id": "req_...",
  "ok": true,
  "data": {
    "items": [
      {
        "submission_id": "subm_01J...",
        "memory_type": "failure_pattern",
        "scope": "global",
        "pii_risk_score": 0.04,
        "policy_risk_score": 0.12,
        "quality_score": 0.81,
        "dedupe_similarity": 0.67,
        "preview": {
          "title": "Avoid sync sqlite3 in async FastAPI route",
          "summary": "..."
        }
      }
    ]
  }
}
~~~

### 5.6 Moderation decision

Method and path:
- POST /moderation/decision

Request:
~~~json
{
  "submission_id": "subm_01J...",
  "decision": "approve",
  "reason_code": "quality_pass",
  "notes": "Good reproduction and prevention rule",
  "publish_scope": "global"
}
~~~

Response:
~~~json
{
  "request_id": "req_...",
  "ok": true,
  "data": {
    "submission_id": "subm_01J...",
    "moderation_state": "approved",
    "published_pattern_id": "pat_01J..."
  }
}
~~~

Decision enum:
- approve
- reject
- quarantine
- escalate

---

## 6. Schema Fields (Storage Layer)

Primary store:
- PostgreSQL + pgvector

### 6.1 Table: databank_patterns

- pattern_id (uuid, pk)
- scope (enum: global, team)
- team_id (uuid, nullable)
- memory_type (enum: success_pattern, failure_pattern, project_rule)
- title (varchar 140)
- summary (text)
- prevention_rule (text, nullable)
- corrected_approach (text, nullable)
- language (varchar 64, nullable)
- framework (varchar 64, nullable)
- tags (jsonb)
- embedding (vector(1536))
- content_hash (varchar 80)
- confidence (double precision)
- quality_score (double precision)
- trust_score (double precision)
- acceptance_rate (double precision)
- report_rate (double precision)
- usage_count (integer)
- freshness_last_seen_at (timestamptz)
- policy_risk_score (double precision)
- pii_risk_score (double precision)
- moderation_state (enum: queued, approved, rejected, quarantined, deprecated)
- source_submission_id (uuid)
- source_license (varchar 32)
- created_at (timestamptz)
- updated_at (timestamptz)

Indexes:
- idx_databank_patterns_scope_type (scope, memory_type)
- idx_databank_patterns_lang_fw (language, framework)
- idx_databank_patterns_state (moderation_state)
- idx_databank_patterns_embedding (ivfflat/hsnw depending on pgvector strategy)

### 6.2 Table: databank_submissions

- submission_id (uuid, pk)
- contributor_id (uuid)
- scope_requested (enum: global, team)
- memory_type (enum)
- payload_json (jsonb)
- content_hash (varchar 80)
- dedupe_status (enum: new, duplicate, merged)
- dedupe_target_pattern_id (uuid, nullable)
- quality_score_initial (double precision)
- policy_risk_score_initial (double precision)
- pii_risk_score_initial (double precision)
- moderation_state (enum: queued, approved, rejected, quarantined, escalated)
- moderation_priority (smallint)
- created_at (timestamptz)
- updated_at (timestamptz)

### 6.3 Table: databank_feedback_events

- feedback_id (uuid, pk)
- result_id (uuid)
- contributor_id (uuid)
- action (enum: accepted, rejected, edited_then_accepted, reported_incorrect)
- resolved_issue (boolean, nullable)
- agent_source (varchar 128, nullable)
- created_at (timestamptz)

### 6.4 Table: databank_moderation_events

- moderation_event_id (uuid, pk)
- submission_id (uuid)
- moderator_id (uuid)
- decision (enum: approve, reject, quarantine, escalate)
- reason_code (varchar 64)
- notes (text)
- created_at (timestamptz)

### 6.5 Table: contributor_profiles

- contributor_id (uuid, pk)
- reputation_score (double precision)
- trust_tier (enum: new, trusted, verified)
- accepted_submissions (integer)
- rejected_submissions (integer)
- reports_received (integer)
- is_suspended (boolean)
- created_at (timestamptz)
- updated_at (timestamptz)

---

## 7. Ranking Formula

Rank each candidate on a normalized 0..1 scale.

Let:
- S_sem = semantic similarity (embedding cosine)
- S_lex = lexical similarity (BM25 or trigram)
- S_lang = language match score
- S_fw = framework match score
- S_q = quality_score
- S_t = trust_score
- S_f = freshness decay score
- S_a = acceptance_rate
- S_scope = scope boost (team > global)
- P_risk = policy risk penalty
- P_dup = near-duplicate penalty

Final score:

S_final =
  w_sem*S_sem +
  w_lex*S_lex +
  w_lang*S_lang +
  w_fw*S_fw +
  w_q*S_q +
  w_t*S_t +
  w_f*S_f +
  w_a*S_a +
  w_scope*S_scope -
  w_risk*P_risk -
  w_dup*P_dup

Default weights:
- w_sem = 0.30
- w_lex = 0.10
- w_lang = 0.08
- w_fw = 0.08
- w_q = 0.14
- w_t = 0.08
- w_f = 0.06
- w_a = 0.10
- w_scope = 0.06
- w_risk = 0.16
- w_dup = 0.06

Freshness function:
- S_f = exp(-age_days / 60)

Gating rules before ranking:
- moderation_state must be approved
- policy_risk_score < 0.5
- pii_risk_score < 0.3

Tie-breakers:
1. Higher acceptance_rate
2. Higher trust_score
3. Lower age_days
4. Lower report_rate

---

## 8. Moderation Workflow

States:
- submitted
- redaction_checked
- dedupe_checked
- queued
- approved
- rejected
- quarantined
- published
- deprecated

### 8.1 Workflow stages

1. Client submission accepted
- Persist to databank_submissions
- Run redaction verifier and policy classifier

2. Automated triage
- If pii_risk_score >= 0.3: set quarantined
- If policy_risk_score >= 0.5: set queued with high priority
- Compute dedupe similarity against existing patterns

3. Dedupe path
- If similarity >= 0.95: merge into existing pattern, increment usage stats
- Else keep as new candidate

4. Human moderation
- Moderator reviews preview, risk metrics, and nearest neighbors
- Decision: approve, reject, quarantine, escalate

5. Publish
- On approve, create or update databank_patterns row with moderation_state=approved
- Emit sync event for downstream clients

6. Continuous quality
- Aggregate feedback events
- Auto-deprecate if report_rate exceeds threshold and acceptance drops

### 8.2 SLA targets

- Automated triage: < 10 sec
- Standard moderation queue: < 60 min
- High-risk queue: < 15 min

### 8.3 Audit requirements

- Every moderation decision writes immutable moderation_event
- Decision must include reason_code
- Keep 1 year of moderation history minimum

---

## 9. Privacy, Security, and Compliance

1. Redaction before upload
- Strip secrets, API keys, hostnames, emails, private paths.

2. Data minimization
- Upload summary and rule text by default.
- Raw code snippets only when user explicitly allows and policy permits.

3. Access control
- JWT with Pro entitlement claim.
- Role-based endpoints for moderators.

4. Abuse prevention
- Rate limits per user and install ID.
- Reputation throttle for new contributors.
- Automatic suspension on repeated policy violations.

5. Deletion/takedown
- Contributor can request submission deletion.
- Moderator emergency unpublish endpoint required.

---

## 10. Extension and Service Integration

### Local service changes

- Add Pro sync adapter module:
  - submit_contribution()
  - search_shared()
  - send_feedback()
  - sync_updates()

- Add settings:
  - vibecode.pro.enabled (bool)
  - vibecode.pro.scope (global/team)
  - vibecode.pro.upload_opt_in (bool)
  - vibecode.pro.include_raw_snippets (bool)
  - vibecode.pro.max_shared_results (int)

### Extension UX changes

- Contribution preview dialog before first upload.
- Source badges in result list:
  - local
  - team databank
  - global databank
- Feedback actions in UI:
  - Helpful
  - Not helpful
  - Report issue

---

## 11. Acceptance Criteria

1. User can opt in and submit a sanitized contribution.
2. Submission appears in moderation queue with risk and quality metrics.
3. Moderator approve action publishes pattern.
4. Another Pro client can retrieve published pattern via search.
5. Ranking returns local results first when scores are comparable.
6. Feedback events modify acceptance_rate and influence ranking within 15 min.
7. Quarantined items are never returned by search.
8. All moderation actions are auditable.

---

## 12. Testing Plan

### Unit tests

- Ranking formula normalization and weighting
- Risk gating behavior
- Dedupe merge logic
- Reputation updates from feedback

### Integration tests

- Contribution -> moderation -> publish -> search flow
- Team scope isolation
- Token entitlement enforcement
- Quarantine path exclusion from search

### Security tests

- Redaction effectiveness on secret fixtures
- AuthZ tests for moderator endpoints
- Rate-limit and abuse scenarios

---

## 13. Rollout Plan

Phase A (internal):
- Read-only shared retrieval from curated seed set

Phase B (beta Pro):
- Opt-in submissions with human moderation only

Phase C (GA Pro):
- Reputation-assisted moderation and team-scoped databanks

---

## 14. Future Enhancements

- Contributor trust graph
- Org-private policy packs
- Auto-cluster and summarize near-duplicate patterns
- Marketplace-facing quality badges for highly reliable patterns
