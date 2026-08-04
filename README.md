# ableton-mcp

An MCP server to control Ableton Live via the Live API.

Live's API is only reachable from Python running inside Live, so this is two
processes talking over TCP on localhost:

- `remote_script/AbletonMCP` runs inside Live as a control surface. It polls a
  non-blocking socket from Live's main thread on a 100ms tick, so every
  command runs on the main thread and no threading hacks are needed.
- `src/ableton_mcp` is the MCP server. It translates tool calls into bridge
  commands over a length-prefixed JSON protocol.

## What it can do

41 tools across two layers.

Curated tools:

- Transport and song: play/stop, tempo, time signature, loop region,
  quantization, undo/redo, cue points
- Tracks: create/delete/duplicate (MIDI, audio, return), name/color/arm/
  mute/solo, monitoring, input/output routing
- Scenes: create/delete/duplicate/fire
- Clips: session and arrangement, create/delete/fire, loop points, markers,
  launch settings, warp/gain/pitch, place session clips on the timeline
- MIDI notes: read, add, update, and remove by stable note ID, so existing
  clips can be edited instead of overwritten
- Mixer: volume, pan, sends, crossfader, with display strings ("0.0 dB")
- Devices: list (including rack chains and drum pads), read parameters, set
  by name or option, delete
- Automation: write/read/clear clip envelopes on any device or mixer
  parameter
- Browser: navigate, search, and load instruments/effects/presets onto a
  track

Generic layer: `live_get`, `live_set`, `live_call`, and `live_describe` reach
the entire Live Object Model through paths like
`song.tracks[0].devices[0].parameters[3]`, covering anything the curated
tools don't.

Not done yet: a change-event feed (listeners) and an installer script.

## Setup

Requires Live 11 or newer and [uv](https://docs.astral.sh/uv/).

1. Install the remote script (`--symlink` if you're hacking on it):

```sh
uv run python scripts/install_remote_script.py
```

2. Restart Live, then pick AbletonMCP as a control surface under
   Settings > Link, Tempo & MIDI.
3. Register the server with your MCP client. The `--directory` value is the
   absolute path to this cloned repo (the install script prints a config
   with the path filled in):

```json
{
  "mcpServers": {
    "ableton-live": {
      "command": "uv",
      "args": ["run", "--directory", "/Users/you/dev/ableton-mcp", "ableton-mcp"]
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
running. CI runs them on every pull request.

With Live open and the control surface enabled, the integration suite does
real round trips (creates and deletes a scratch track):

```sh
ABLETON_MCP_LIVE_TESTS=1 uv run pytest tests/integration -v
```

Releases are tagged from main; see CHANGELOG.md.
