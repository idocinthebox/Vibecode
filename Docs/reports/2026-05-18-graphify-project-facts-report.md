# Graphify Project Facts Report

- Date: 2026-05-18
- Repository: Vibecode
- Branch: main
- Commit: f6c80fe6739324d7b69f739140f7bdf5460c5198
- Git root verified: D:/Vibecoder

## Scope

Use Graphify outputs to identify project facts and relationships relevant to VibeCode harvest and auto-capture flows.

## Data Source

- File analyzed: graphify-out/graph.json
- Build status: parseable JSON graph artifact exists
- Graph size observed: 1403 nodes, 0 edges

## Verified Symbol Facts

1. VibeCodeService -> vibecode/core/memory_service.py (L40)
2. OutcomeTracker -> vibecode/core/outcome_tracker.py (L33)
3. AutoCaptureService -> vibecode/core/auto_capture_service.py (L11)
4. maybePromptHarvestOnActivation() -> vibe-code-extension/src/extension.ts (L234)
5. workspaceHasHarvestSources() -> vibe-code-extension/src/extension.ts (L269)
6. registerHarvestProjectKnowledgeCommand() -> vibe-code-extension/src/commands/harvestProjectKnowledgeCommand.ts (L12)
7. VibeCodeApiClient.harvestScan() -> vibe-code-extension/src/services/apiClient.ts (L94)
8. harvest_scan() route -> vibecode/api/routes_harvest.py (L17)
9. harvest_preview() route -> vibecode/api/routes_harvest.py (L32)
10. harvest_report() route -> vibecode/api/routes_harvest.py (L47)
11. harvest_scan() CLI command -> vibecode/cli/app.py (L397)
12. harvest_preview() CLI command -> vibecode/cli/app.py (L411)
13. harvest_report() CLI command -> vibecode/cli/app.py (L424)

## Relationship Findings

- Direct relationship/path tracing is currently blocked in this graph build because edges = 0.
- Community clustering still provides coarse relationship signals:
  - Community 6 groups VibeCodeService, OutcomeTracker, AutoCaptureService, and related tests.
  - Community 1 groups extension activation and command registration symbols, including harvest prompt logic.
  - Community 13 groups extension API client transport methods, including harvestScan/harvestPreview/harvestReport.

## Known Tooling Limits

- Installed Graphify version observed in session: 0.4.39.
- `graphify explain` and `graphify path` are currently unreliable in this environment due to an upstream `UnboundLocalError` (`json` variable reference).
- `graphify vscode-build . --deep` reports that VS Code command path is AST-only and suggests semantic integration via `--update` or AI chat rebuild flow.

## Rebuild Experiment (This Run)

Goal: produce non-zero edges for path-level relationship tracing.

1. Baseline check after `graphify vscode-build .`: 1403 nodes, 0 edges.
2. `graphify update .` completed full extraction (254/254): graph remained 1403 nodes, 0 edges.
3. `graphify vscode-build . --deep` completed full extraction (254/254): graph remained 1403 nodes, 0 edges.

Conclusion: with current Graphify 0.4.39 behavior in this environment, rebuild mode changes do not produce edges for this repository snapshot.

## Tests and Validation

- Commands run and successful:
  - `vibecode service status` (exit code 0)
  - graph JSON parsing and symbol extraction one-liners via `.venv\\Scripts\\python.exe` (exit code 0)
- Not run in this reporting step:
  - `pytest`
  - extension integration tests

## Changes Made

- Added this report file.
- Appended rebuild experiment results in this run.
- No source code behavior changes.

## Follow-ups

1. Rebuild Graphify output with settings/mode that emit call/import edges, then rerun path checks.
2. Pin or upgrade Graphify to a version where `explain`/`path` no longer throw `UnboundLocalError`.
3. After edge generation works, validate expected harvest flow chain from extension activation to API route handlers.
