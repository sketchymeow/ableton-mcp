# ableton-mcp

MCP server that controls Ableton Live. Two processes: a remote script inside
Live and a FastMCP server, talking over TCP on 127.0.0.1:9877 with 4-byte
length-prefixed JSON frames.

## Commands

- `uv sync` — install deps (always uv, never pip)
- `uv run pytest` — unit tests, no Live needed (fake LOM in tests/unit/fake_live.py)

## Architecture rules

- `remote_script/AbletonMCP/` runs inside Live's embedded Python:
  - Python 3.7-safe syntax only (Live 11 floor), stdlib only, no third-party deps.
  - No threads. `BridgeServer.tick()` is pumped from Live's main thread every
    ~100ms via `schedule_message(1, ...)`. The Live API is main-thread only;
    the tick model makes that hold by construction.
  - `__init__.py` must stay importable outside Live: anything touching
    `Live` or `ableton.v2` imports lazily (see surface.py / handlers/raw.py).
- `src/ableton_mcp/` is the MCP server (Python 3.11+, FastMCP).
- `protocol.py` exists twice on purpose (remote script must be self-contained,
  Live loads it from a folder). Edit both copies; a unit test fails if they drift.
- One command registry dict in the remote script. Never maintain parallel
  command lists (the project this replaces had three that desynced).
- Socket binds 127.0.0.1 only. Keep it that way.

## Workflow

- One commit per plan phase. PLAN.md is untracked via .git/info/exclude and
  must never be committed.
- Adding a bridge command: register it in a handler module under
  `remote_script/AbletonMCP/handlers/`, expose it as an MCP tool in
  `src/ableton_mcp/server.py`, add a unit test against the fake LOM.

## Live API notes

- Note editing uses the Live 11+ APIs: `get_notes_extended`, `add_new_notes`,
  `apply_note_modifications`, `remove_notes_extended` (stable note IDs).
- Reference implementations cloned for study (scratchpad, not in repo):
  ideoforms/AbletonOSC (LOM breadth, listeners) and ahujasid/ableton-mcp
  (browser loading). Neither has automation envelopes; we build those.
- Live float properties reject ints; the bridge retries `setattr` with
  `float(value)` on TypeError.
