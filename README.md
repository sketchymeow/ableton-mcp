# ableton-mcp

An MCP server to control Ableton Live via the Live API.

Live's API is only reachable from Python running inside Live, so this is two
processes talking over TCP on localhost:

- `remote_script/AbletonMCP` runs inside Live as a control surface. It polls a
  non-blocking socket from Live's main thread on a 100ms tick, so every
  command runs on the main thread and no threading hacks are needed.
- `src/ableton_mcp` is the MCP server. It translates tool calls into bridge
  commands over a length-prefixed JSON protocol.

## Status

Early. The generic layer works: `ping`, `live_get`, `live_set`, `live_call`,
and `live_describe` reach the whole Live Object Model through paths like
`song.tracks[0].devices[0].parameters[3]`. Curated tools for tracks, clips,
notes, devices, automation, and the browser come next.

## Setup

Requires Live 11 or newer and [uv](https://docs.astral.sh/uv/).

1. Copy `remote_script/AbletonMCP` into your User Library under
   `Remote Scripts/` (create the folder if it doesn't exist).
2. Restart Live, then pick AbletonMCP as a control surface under
   Settings > Link, Tempo & MIDI.
3. Register the server with your MCP client:

```json
{
  "mcpServers": {
    "ableton-live": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/ableton-mcp", "ableton-mcp"]
    }
  }
}
```

## Development

```sh
uv sync
uv run pytest
```

Unit tests run against a fake Live object model, so they don't need Live
running.
