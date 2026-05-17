# VibeCode 🧠⚡

**Token-efficient AI coding assistant with persistent reasoning memory.**

VibeCode builds a local memory bank of your successful patterns, failed attempts, and project rules — so your AI assistant stops regenerating the same reasoning from scratch every session. Instead of burning 70% of your API budget on redundant context, retrieve distilled knowledge in a few tokens.

---

## Why VibeCode?

| Without VibeCode | With VibeCode |
|---|---|
| AI re-explains project conventions every prompt | Rules & patterns retrieved automatically |
| Failed approaches tried again and again | Failures memorized; warnings shown inline |
| Success patterns lost after the chat ends | Success patterns stored, searchable, reusable |
| Token bills grow linearly with usage | 60-80% token reduction on repeated tasks |

---

## Features

### 🧩 Memory Bank

- **Success Patterns** — Save working solutions with context, reasoning traces, and token metrics.
- **Failure Patterns** — Capture what went wrong and why; prevention rules surface as inline warnings.
- **Project Rules** — Codify conventions ("use Pydantic v2", "no sync DB calls in async handlers") once.

### 🔁 Auto-Capture Loop (Packet 5)

- **Agent edit observation** — Tracks agent-authored edits and correlates them with diagnostics, test outcomes, reverts, and terminal results.
- **Automatic success/failure capture** — Stores recurring outcomes with confidence, occurrence counts, agent source, and review state.
- **Pre-edit guardrail** — New pre-edit check endpoint and MCP tool return matching failure rules before an agent writes code.
- **Review queue** — Pending auto-captures can be confirmed or discarded from the extension sidebar.

### 🔌 Multi-Interface

| Interface | Status | Description |
|---|---|---|
| **VSCode Extension** | ✅ Active | Sidebar memory browser, inline diagnostics, hover tooltips, quick-fix code actions |
| **CLI (Rich/Typer)** | ✅ Active | `search`, `inject`, `capture-success/failure`, `add-rule`, `report`, `doctor`, `config` |
| **MCP Server** | ✅ Active | Native integration with Claude Code, Cursor, and any MCP client |
| **Local HTTP API** | ✅ Active | FastAPI service on `127.0.0.1:8765` for custom tooling |

### 🛡️ Privacy & Security

- **100% local by default** — SQLite backend; optional PostgreSQL for teams.
- **Secret redaction** — API keys, passwords, and private keys stripped before storage.
- **Project allowlist** — Only explicitly allowed project paths can write to the memory bank.
- **No cloud telemetry** — Your code never leaves your machine.

### 📊 Token Economics

- Tracks estimated tokens saved per retrieval.
- Reports show daily/weekly savings and hit rates.
- Context injection respects a token budget; prioritizes high-confidence failure warnings.

---

## Quick Start

### 1. Install the Python service

```bash
pip install -e .
vibecode init
vibecode service start
```

The service binds to `127.0.0.1:8765` by default.

### 2. Install the VSCode extension

```bash
cd vibe-code-extension
npm install
npx vsce package --no-dependencies
code --install-extension vibe-code-0.1.0.vsix
```

Or install directly from the VSIX in the repo releases.

### 3. Capture your first pattern

**CLI:**

```bash
vibecode capture-success --name "FastAPI dependency injection" \
  --intent "Refactor DB session to dependency" \
  --language python --framework fastapi
```

**VSCode:**
Select code → Right-click → **VibeCode: Capture Success Pattern**

### 4. Inject context into your next prompt

```bash
vibecode inject --query "Add auth middleware to this route" --output context.md
```

---

## Architecture

```
┌─────────────────────────────────────────┐
│  VSCode Extension    │  CLI / MCP       │
│  (TypeScript)        │  (Python/Rich)   │
└──────────┬───────────┴────────┬─────────┘
           │                    │
           └────────┬───────────┘
                    │ HTTP (localhost)
           ┌────────▼───────────┐
           │  FastAPI Service   │
           │  127.0.0.1:8765    │
           └────────┬───────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
   ┌────────┐ ┌──────────┐ ┌──────────┐
   │ SQLite │ │PostgreSQL│ │  Search  │
   │(default)│ │(optional)│ │  Index   │
   └────────┘ └──────────┘ └──────────┘
```

---

## VSCode Extension Highlights

- **Activity Bar Sidebar** — Browse failure warnings, project rules, and success patterns.
- **Inline Warnings** — Squiggly underlines when your code matches a known failure pattern; hover for prevention rules.
- **Code Actions** — `Generate Agent Context`, `Search Related Memory`, `Ignore Warning`, `Capture as Failure`.
- **Status Bar** — Live service connection indicator.

---

## CLI Commands

```
vibecode init              # Initialize storage and config
vibecode search <query>    # Search memory bank
vibecode inject <query>    # Build context markdown for agents
vibecode capture-success   # Save a working pattern
vibecode capture-failure   # Save a failed approach
vibecode add-rule          # Add a project convention rule
vibecode report            # Show token savings and stats
vibecode doctor            # Check service health and setup
vibecode config            # View/edit settings
```

---

## MCP Integration

Add to your Claude/Cursor MCP config:

```json
{
  "mcpServers": {
    "vibecode": {
      "command": "vibecode",
      "args": ["mcp", "run"]
    }
  }
}
```

Tools exposed: `search_memory`, `inject_context`, `capture_failure`, `pre_edit_check`, `get_current_context`.

---

## Development

### Python Tests

```bash
pytest tests/ -v
# Includes Packet 5 suites for outcome tracking, auto-capture, review routes, and MCP pre-edit checks
```

### Extension Tests

```bash
cd vibe-code-extension
npm run compile
npm run test
# 39 passing
```

### Build VSIX

```bash
npm run compile
npx vsce package --no-dependencies
```

---

## Tech Stack

| Layer | Tech |
|---|---|
| Service | Python 3.12, FastAPI, SQLAlchemy, SQLite/PostgreSQL |
| CLI | Typer, Rich, Pydantic |
| Extension | TypeScript, VSCode API, Webpack |
| Tests | pytest (Python), Mocha (TypeScript) |
| Packaging | setuptools, vsce |

---

## Roadmap

- [x] SQLite persistence & JSON migration
- [x] Local HTTP API + project allowlist
- [x] MCP server
- [x] Rich CLI with `doctor`, `report`, `config`
- [x] VSCode extension scaffold
- [x] VSCode sidebar (memory browser + stats)
- [x] VSCode inline warnings + code actions
- [ ] Vector semantic search (pgvector)
- [ ] Automatic pattern capture from git diffs
- [ ] Team sync / shared PostgreSQL backend
- [ ] Cursor/JetBrains plugins

---

## License

MIT
