# VibeCode VSCode Extension

Thin client for the VibeCode local AI coding memory service.

## Packet 5 Features

- Automatic agent edit observation and outcome reporting to the local service
- Auto-capture notifications when VibeCode learns new success/failure patterns
- Pending review queue sidebar for confirm/discard flows
- Auto-correct context writer to `.vibecode/agent-context.md` when agent sessions start
- Corrected-approach quick fix when a diagnostic includes a known fix snippet

## Requirements

- VibeCode local service running on `http://127.0.0.1:8765`
- Run `vibecode service start` in a terminal

## Commands

| Command | Description |
|---------|-------------|
| `VibeCode: Search VibeCode Memory` | Search memory patterns |
| `VibeCode: Generate Agent Context` | Inject context for current task |
| `VibeCode: Capture Selection as Success Pattern` | Save selected code as success |
| `VibeCode: Capture Selection as Failure Warning` | Save selected code as failure |
| `VibeCode: Confirm Auto-Captured Pattern` | Confirm an item in the pending review queue |
| `VibeCode: Discard Auto-Captured Pattern` | Discard an item in the pending review queue |
| `VibeCode: Open Auto-Capture Review Queue` | Focus the pending review sidebar |
| `VibeCode: Check VibeCode Service Status` | Check local service health |
| `VibeCode: Open VibeCode Settings` | Open extension settings |

## Build

```bash
npm install
npm run compile
npm run package
npm run vsix
```

## Test

```bash
npx tsc -p .
npm test
```

## Install from VSIX

```bash
code --install-extension vibe-code-0.1.0.vsix
```
