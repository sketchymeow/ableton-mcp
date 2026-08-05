# ableton-mcp

MCP server that controls Ableton Live. Two processes: a Python remote script
inside Live and a TypeScript MCP server, talking over TCP on 127.0.0.1:9877
with 4-byte length-prefixed JSON frames.

## Commands

- `uv sync && uv run pytest` — remote script tests, no Live needed (fake LOM
  in tests/unit/fake_live.py). Always uv, never pip.
- `cd server && npm install && npm test` — MCP server tests (vitest)
- `cd server && npx tsc --noEmit` — typecheck
- `cd server && npm run build` — esbuild bundle to server/dist/index.js
  (includes a stdio initialize smoke test)
- `cd server && npm run build:mcpb` — Claude Desktop bundle (node-type,
  packed with the official mcpb CLI)

## Architecture rules

- `remote_script/AbletonMCP/` runs inside Live's embedded Python:
  - Python 3.7-safe syntax only (Live 11 floor), stdlib only, no third-party
    deps. All the real logic lives here.
  - No threads. `BridgeServer.tick()` is pumped from Live's main thread every
    ~100ms via `schedule_message(1, ...)`. The Live API is main-thread only;
    the tick model makes that hold by construction.
  - `__init__.py` must stay importable outside Live: anything touching
    `Live` or `ableton.v2` imports lazily (see surface.py, handlers).
- `server/` is the MCP server: TypeScript, `@modelcontextprotocol/server`
  v2 (`McpServer`, `serveStdio`, zod v4 schemas). Tools are thin wrappers;
  trivial one-property reads/writes go through the generic bridge commands
  (get_property/set_property/call_method); the bridge only gains commands
  for compound reads, batched writes, or logic that needs Live-side context.
- `server/src/protocol.ts` must stay wire-compatible with
  `remote_script/AbletonMCP/core/protocol.py`. Both have framing tests.
- One command registry dict in the remote script. Never maintain parallel
  command lists.
- Socket binds 127.0.0.1 only. Keep it that way.
- MCP clients stringify numbers on union-typed fields; the bridge coerces
  numeric strings everywhere a float is expected. Don't remove that.
- Object-valued LOM properties (routing, selected_*) can't take scalars:
  set_property resolves against the available_* sibling list, or takes a
  value_path. Live float properties reject ints and strings (Boost.Python
  TypeError) — set_with_float_retry handles it.

## Workflow

- PLAN.md is untracked via .git/info/exclude and must never be committed.
- Update CHANGELOG.md (Keep a Changelog format) with user-visible changes;
  releases are annotated git tags (vX.Y.Z) matching server/package.json.
  Tag pushes build the .mcpb and attach it to the GitHub release.
- Adding a bridge command: register it in a handler module under
  `remote_script/AbletonMCP/handlers/`, expose it as a tool in
  `server/src/tools/`, add a pytest against the fake LOM.
- Reloading after changes: remote script changes need a Live restart (or
  toggling the control surface); server/tool-schema changes need a Claude
  Desktop restart. The user's install is symlinked to this repo.
- Integration tests need Live running: ABLETON_MCP_LIVE_TESTS=1
  uv run pytest tests/integration.

## Live API notes

- Note editing uses the Live 11+ APIs: `get_notes_extended`, `add_new_notes`,
  `apply_note_modifications`, `remove_notes_extended` (stable note IDs).
- Reference implementations studied: ideoforms/AbletonOSC (LOM breadth,
  listeners) and ahujasid/ableton-mcp (browser loading). Neither has
  automation envelopes; we built those.
- Browser results are capped (browse paged at 500, search at 100 matches)
  because Claude Desktop rejects tool results over 1MB.
