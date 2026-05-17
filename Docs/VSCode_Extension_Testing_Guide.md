# VibeCode VSCode Extension — Testing Guide

**Extension path:** `D:\Vibecode\vibe-code-extension`  
**Python backend:** `D:\Vibecoder` (must be running for integration tests)  
**Test suite:** 39 Mocha unit tests + manual VSCode integration tests

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Automated Unit Tests](#automated-unit-tests)
3. [Type Checking & Linting](#type-checking--linting)
4. [Build Verification](#build-verification)
5. [Manual Testing in VSCode](#manual-testing-in-vscode)
6. [VSIX Packaging & Installation](#vsix-packaging--installation)
7. [Troubleshooting](#troubleshooting)
8. [Pre-Release Checklist](#pre-release-checklist)

---

## Prerequisites

### 1. Install Node dependencies

```bash
cd D:\Vibecode\vibe-code-extension
npm install
```

### 2. Start the Python backend

The extension is a thin client. Most features require the local FastAPI service running on `127.0.0.1:8765`.

```bash
cd D:\Vibecoder
python -m vibecode init        # One-time setup
python -m vibecode service start
```

Verify the service is up:
```bash
curl http://127.0.0.1:8765/health
```

### 3. Seed some test data

```bash
cd D:\Vibecoder

# Add current project to allowlist
python -m vibecode project allow D:\Vibecoder

# Capture a success pattern
python -m vibecode capture-success \
  --project D:\Vibecoder \
  --name "FastAPI dependency injection" \
  --intent "Refactor DB session to FastAPI dependency" \
  --language python \
  --framework fastapi

# Capture a failure pattern (will trigger inline warnings)
python -m vibecode capture-failure \
  --project D:\Vibecoder \
  --task-intent "Use synchronous DB calls in async handler" \
  --bad-suggestion "Use sqlite3 directly in FastAPI endpoint" \
  --failure-reason "Blocks the event loop, kills concurrency" \
  --prevention-rule "Always use async SQLAlchemy or aiosqlite in async handlers" \
  --severity high \
  --language python

# Add a project rule
python -m vibecode add-rule \
  --project D:\Vibecoder \
  --text "Use Pydantic v2 models for all request/response schemas" \
  --type "architecture" \
  --severity high
```

---

## Automated Unit Tests

These tests run **outside VSCode** using a mocked `vscode` module. They verify API clients, command registration, sidebar logic, diagnostics, and code actions without launching a real editor.

### Run all tests

```bash
cd D:\Vibecode\vibe-code-extension

# Compile TypeScript
npx tsc --outDir out

# Run the full suite
npx mocha --ui tdd --require out/test/setup.js "out/test/suite/*.test.js"
```

### Expected output

```
  39 passing (129ms)
```

### Run individual test files

```bash
npx mocha --ui tdd --require out/test/setup.js out/test/suite/apiClient.test.js
npx mocha --ui tdd --require out/test/setup.js out/test/suite/diagnosticProvider.test.js
npx mocha --ui tdd --require out/test/setup.js out/test/suite/codeActionProvider.test.js
npx mocha --ui tdd --require out/test/setup.js out/test/suite/suppressionService.test.js
npx mocha --ui tdd --require out/test/setup.js out/test/suite/memoryBrowserService.test.js
```

### Test coverage by file

| Test file | What it tests |
|---|---|
| `apiClient.test.js` | HTTP client health, search, inject endpoints |
| `commandRegistration.test.js` | Commands declared in `package.json`, activation events |
| `extension.test.js` | Extension activates, API client instantiates |
| `workspaceService.test.js` | Path normalization, subpath detection |
| `sidebarCommands.test.js` | Views, menus, sidebar command registration |
| `memoryTreeProvider.test.js` | Tree items, group labels, offline state |
| `memoryBrowserService.test.js` | Refresh, sort by severity, preview markdown |
| `diagnosticProvider.test.js` | Secret file skipping, severity mapping |
| `suppressionService.test.js` | Read/write `.vscode/vibecode-suppressions.json` |
| `codeActionProvider.test.js` | Quick-fix actions on VibeCode diagnostics |

---

## Type Checking & Linting

### TypeScript compiler (no emit)

```bash
cd D:\Vibecode\vibe-code-extension
npx tsc --noEmit
```

**Pass criteria:** No errors.

### ESLint

```bash
cd D:\Vibecode\vibe-code-extension
npm run lint
```

**Pass criteria:** No lint errors.

---

## Build Verification

### Development build

```bash
cd D:\Vibecode\vibe-code-extension
npm run compile
```

**Pass criteria:** Webpack compiles successfully. Output:
- `out/extension.js` (~134KB)
- `out/extension.js.map`

### Production build

```bash
cd D:\Vibecode\vibe-code-extension
npm run package
```

**Pass criteria:** Minified bundle created. Output:
- `out/extension.js` (~40KB)

### Watch mode (for development)

```bash
cd D:\Vibecode\vibe-code-extension
npm run watch
```

Rebuilds automatically when source files change.

---

## Manual Testing in VSCode

This is the most important validation step. You test the extension **inside a real VSCode instance**.

### Launch the Extension Development Host

1. Open the extension folder in VSCode:
   ```bash
   code D:\Vibecode\vibe-code-extension
   ```

2. Inside that VSCode window, press **F5** (or `Run → Start Debugging`).

3. A **new VSCode window** opens with your extension loaded. This is the "Extension Development Host."

4. In the new window, open a project folder that has been added to the VibeCode allowlist (e.g. `D:\Vibecoder`).

### Test Commands

Open the Command Palette: `Ctrl+Shift+P` → type each command:

| Command | Expected Result |
|---|---|
| `VibeCode: Search Memory` | Quick-pick opens, shows search results from backend |
| `VibeCode: Generate Agent Context` | Context markdown generated, shown in output channel |
| `VibeCode: Capture Selection as Success Pattern` | Captures selected code (requires text selection) |
| `VibeCode: Capture Selection as Failure Warning` | Captures selected code as failure |
| `VibeCode: Check VibeCode Service Status` | Shows "Ready" or "Offline" notification |
| `VibeCode: Open Settings` | Opens VSCode settings with `vibeCode.` filter |

### Test Sidebar (Activity Bar)

1. Look for the **VibeCode** icon in the left Activity Bar (it may be near the Explorer icon).

2. **Memory Browser** (`vibeCodeMemory` view):
   - Should show groups: "Failure Warnings", "Project Rules", "Success Patterns"
   - Click the refresh 🔄 button to reload from backend
   - Click a memory item to preview its details
   - Right-click a memory item to copy context

3. **Stats** (`vibeCodeStats` view):
   - Should show estimated tokens saved

### Test Inline Warnings (Packet 4C)

1. Open a Python file in an allowed project.

2. Write code that matches a captured failure pattern. For example, if you captured a failure about sync DB calls:
   ```python
   import sqlite3
   
   def get_user(user_id: int):
       conn = sqlite3.connect("users.db")  # <-- may trigger inline warning
       return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
   ```

3. **Expected:** After ~1.5 seconds (debounce), a yellow/orange squiggly underline appears under the matching code.

4. **Hover** over the underline → a Markdown tooltip appears showing:
   - Severity level
   - Prevention rule
   - Why it matched
   - Action buttons (Generate Context, Search Related, Ignore)

5. **Click the 💡 lightbulb** (or press `Ctrl+.` ) → Code Actions menu appears:
   - `Generate Agent Context From Diagnostic`
   - `Search Related Memory`
   - `Ignore This Warning`
   - `Capture as Failure`

### Test Settings

Open VSCode Settings (`Ctrl+,`) and search for `vibeCode`:

| Setting | Test |
|---|---|
| `vibeCode.inlineWarnings.enabled` | Toggle off → warnings disappear |
| `vibeCode.inlineWarnings.minSeverity` | Set to "critical" → only critical warnings show |
| `vibeCode.inlineWarnings.debounceMs` | Set to 500 → warnings appear faster |
| `vibeCode.inlineWarnings.maxDiagnostics` | Set to 2 → only 2 warnings per file |
| `vibeCode.inlineWarnings.checkOnOpen` | Toggle off → no check on file open |
| `vibeCode.inlineWarnings.checkOnSave` | Toggle off → no check on save |

### Test Secret-Sensitive File Skipping

1. Create a `.env` file:
   ```bash
   echo "API_KEY=secret123" > D:\Vibecoder\.env
   ```

2. Open it in VSCode.

3. **Expected:** No inline warnings appear (secret files are automatically skipped).

### Test Suppressions

1. Find a file with an inline VibeCode warning.

2. Click the 💡 lightbulb → `Ignore This Warning`.

3. **Expected:** The warning disappears immediately.

4. Check that `.vscode/vibecode-suppressions.json` was created in the workspace root.

---

## VSIX Packaging & Installation

### Create the VSIX

```bash
cd D:\Vibecode\vibe-code-extension
npm run compile
npx vsce package --no-dependencies
```

**Output:** `vibe-code-0.1.0.vsix` (~88KB, 69 files)

### Install in VSCode

**Option A: Command line**
```bash
cd D:\Vibecode\vibe-code-extension
code --install-extension vibe-code-0.1.0.vsix
```

**Option B: VSCode UI**
1. Press `Ctrl+Shift+P`
2. Run `Extensions: Install from VSIX...`
3. Select `D:\Vibecode\vibe-code-extension\vibe-code-0.1.0.vsix`

**Option C: Drag and drop**
Drag the `.vsix` file into the VSCode Extensions panel (`Ctrl+Shift+X`).

### Reload VSCode

After installation:
```
Ctrl+Shift+P → Developer: Reload Window
```

### Uninstall

```
Ctrl+Shift+X → Search "VibeCode" → Right-click → Uninstall → Reload Window
```

---

## Troubleshooting

### "Cannot find module 'vscode'" during tests

**Cause:** The test runner isn't loading the mock setup.  
**Fix:** Always include `--require out/test/setup.js`:
```bash
npx mocha --require out/test/setup.js ...
```

### Extension shows "Offline" in status bar

**Cause:** The Python service isn't running.  
**Fix:**
```bash
cd D:\Vibecoder
python -m vibecode service start
```

### No inline warnings appear

**Checklist:**
1. Is `vibeCode.inlineWarnings.enabled` set to `true` in settings?
2. Is the Python service running?
3. Is the current project in the VibeCode allowlist?
4. Are there captured failure patterns for this project's language?
5. Is the file a secret-sensitive file (`.env`, `.key`, etc.)?
6. Check the Output panel: `Ctrl+Shift+U` → select "VibeCode" from the dropdown.

### Webpack build fails

```bash
cd D:\Vibecode\vibe-code-extension
rm -rf out node_modules
npm install
npm run compile
```

### VSCode Extension Development Host doesn't open

1. Make sure you're pressing **F5** inside the `D:\Vibecode\vibe-code-extension` workspace.
2. Check `.vscode/launch.json` exists in the extension folder.
3. Try `Run → Start Debugging` from the menu instead of F5.

---

## Pre-Release Checklist

Run this entire sequence before any release:

```bash
# ============================================
# STEP 1: Python backend tests
# ============================================
cd D:\Vibecoder
pytest tests/ -v
# Expected: 71 passed, 19 skipped

# ============================================
# STEP 2: Extension TypeScript type check
# ============================================
cd D:\Vibecode\vibe-code-extension
npx tsc --noEmit
# Expected: No errors

# ============================================
# STEP 3: Extension lint
# ============================================
npm run lint
# Expected: No errors

# ============================================
# STEP 4: Extension unit tests
# ============================================
npx tsc --outDir out
npx mocha --ui tdd --require out/test/setup.js "out/test/suite/*.test.js"
# Expected: 39 passing

# ============================================
# STEP 5: Extension build
# ============================================
npm run compile
# Expected: Webpack success, out/extension.js created

# ============================================
# STEP 6: Production build
# ============================================
npm run package
# Expected: Minified bundle

# ============================================
# STEP 7: VSIX package
# ============================================
npx vsce package --no-dependencies
# Expected: vibe-code-0.1.0.vsix created

# ============================================
# STEP 8: Manual test in VSCode (F5)
# ============================================
# Open D:\Vibecode\vibe-code-extension in VSCode
# Press F5
# Test: sidebar, commands, inline warnings, hovers, code actions

# ============================================
# STEP 9: Install VSIX in main VSCode
# ============================================
code --install-extension vibe-code-0.1.0.vsix
# Reload window
# Test again as an end user would
```

---

## VSCode Extension File Reference

| File | Purpose |
|---|---|
| `src/extension.ts` | Entry point — registers all commands and providers |
| `src/services/apiClient.ts` | HTTP client for `127.0.0.1:8765` |
| `src/services/warningMatchService.ts` | Calls `/memory/search`, maps severity to diagnostic level |
| `src/providers/diagnosticProvider.ts` | Debounced inline warning system |
| `src/providers/hoverProvider.ts` | Hover tooltips on diagnostics |
| `src/providers/codeActionProvider.ts` | 💡 quick-fix actions |
| `src/views/memoryTreeProvider.ts` | Sidebar memory browser |
| `src/views/tokenSavingsProvider.ts` | Sidebar stats view |
| `src/services/suppressionService.ts` | `.vscode/vibecode-suppressions.json` management |
| `test/vscodeMock.ts` | Mock `vscode` module for unit tests |
| `test/setup.ts` | Test bootstrap that swaps `vscode` for the mock |

---

*Generated for VibeCode Packet 4C — VSCode Inline Warnings + Code Actions*
