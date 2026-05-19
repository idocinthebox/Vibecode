<!-- vibecode:begin -->
## VibeCode Agent Instructions

This workspace uses **VibeCode** — a local AI coding memory service that records
success and failure patterns to prevent repeated mistakes and reduce token waste.

When working in this workspace you MUST use the VibeCode MCP tools (exposed by
the local service at http://127.0.0.1:8765 and via MCP stdio):

1. **Before any non-trivial edit** — MUST call `vibecode_inject_context` (or
   `vibecode_search_memory`) with the task intent and target file.
   Read the
   returned failure warnings, project rules, and success patterns before
   proposing code.
2. **On build/test failure** — call `vibecode_capture_failure` with the same
   `task_intent` you used to inject context, plus the failing diff, the error
   output, and the affected files.
3. **On build/test success after a fix** — call `vibecode_capture_success`
   with the same `task_intent` so the win is correlated with the prior
   failure.
4. **At the end of a multi-step task or build phase** — write a short report to
   `Docs/reports/` summarising what changed, commit hashes, test results, and
   any follow-ups.
5. **Never** publish patterns to the shared/Pro databank automatically — that
   action is reserved for the human operator.

If the local service is unreachable, continue normally but log a one-line note
so the user can start it with `vibecode service start`.
<!-- vibecode:end -->
