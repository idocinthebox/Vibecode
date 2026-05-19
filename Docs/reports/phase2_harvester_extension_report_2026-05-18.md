# Phase 2 Build Report (2026-05-18)

## Scope

Implemented Phase 2 features from Build Packet 6/7:
- Full harvest source extractor coverage (ADR, CHANGELOG, linter config, inline rule comments)
- Embedding-based near-duplicate filtering with no-op fallback
- VS Code extension harvest UX (command, init prompt, harvested pending grouping, summary webview)
- Phase 2 backend and extension tests

## Backend Changes

- Added extractors:
  - `vibecode/harvest/extractors/adr.py`
  - `vibecode/harvest/extractors/changelog_fix.py`
  - `vibecode/harvest/extractors/linter_config.py`
  - `vibecode/harvest/extractors/inline_comment.py`
- Updated registry:
  - `vibecode/harvest/extractors/__init__.py`
- Updated markdown extractor routing to avoid overlap:
  - `vibecode/harvest/extractors/markdown_rule.py`
- Expanded walker defaults for inline-source scanning:
  - `vibecode/harvest/walker.py`
- Added semantic dedupe helper and integrated into scan flow:
  - `vibecode/harvest/dedupe.py`
  - `vibecode/harvest/service.py`
- Added pending review support for harvested project rules:
  - `vibecode/repositories/rule_repository.py`
  - `vibecode/core/memory_service.py`
  - `vibecode/api/schemas.py`
- Added `style` as valid `ProjectRule.rule_type`:
  - `vibecode/models/memory_models.py`

## Extension Changes

- Added harvest API types and methods:
  - `vibe-code-extension/src/types/api.ts`
  - `vibe-code-extension/src/services/apiClient.ts`
- Added commands:
  - `vibe-code-extension/src/commands/harvestProjectKnowledgeCommand.ts`
  - `vibe-code-extension/src/commands/confirmHarvestedPendingCommand.ts`
  - `vibe-code-extension/src/commands/discardHarvestedPendingCommand.ts`
- Updated review queue with grouped harvested items and checkbox state support:
  - `vibe-code-extension/src/views/reviewQueueView.ts`
- Updated single-item review commands to support tree node payloads:
  - `vibe-code-extension/src/commands/confirmAutoCaptureCommand.ts`
  - `vibe-code-extension/src/commands/discardAutoCaptureCommand.ts`
- Wired activation behavior:
  - harvest command registration
  - first-run harvest prompt on startup when sources exist
  - checkbox change handling for review queue
  - file: `vibe-code-extension/src/extension.ts`
- Updated manifest for commands, menus, activation events, and harvest settings:
  - `vibe-code-extension/package.json`

## Tests Added

### Backend

- `tests/harvest/test_adr_extractor.py`
- `tests/harvest/test_changelog_fix_extractor.py`
- `tests/harvest/test_linter_config_extractor.py`
- `tests/harvest/test_inline_comment_extractor.py`
- `tests/harvest/test_near_dup.py`
- Fixtures:
  - `tests/fixtures/harvest/ADR-0001.adr.md`
  - `tests/fixtures/harvest/CHANGELOG.md`
  - `tests/fixtures/harvest/pyproject.toml`
  - `tests/fixtures/harvest/inline_rules.py`

### Extension

- `vibe-code-extension/test/suite/harvestCommand.test.ts`
- `vibe-code-extension/test/suite/harvestSidebar.test.ts`
- Updated activation test expectation:
  - `vibe-code-extension/test/suite/commandRegistration.test.ts`

## Validation Results

- Backend harvest/review subset:
  - `pytest tests/harvest tests/test_http_harvest_routes.py tests/test_routes_review.py`
  - Result: `14 passed`
- Extension compile:
  - `npm run compile`
  - Result: success
- Extension tests:
  - `npm test`
  - Result: `49 passing`

## Commits

- No new commit created in this step.

## Follow-ups

- Optional: add backend integration test that scans a temp repo containing both ADR + CHANGELOG and asserts typed outputs in one end-to-end scan.
- Optional: add dedicated command to open `report_path` directly from harvest summary webview.
