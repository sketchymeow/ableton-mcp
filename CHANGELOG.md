# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [SemVer](https://semver.org/).

## [Unreleased]

### Added

- Claude Desktop one-click install: releases ship self-contained .mcpb
  bundles (PyInstaller binary, no Python or uv needed) for Apple silicon,
  Intel mac, and Windows
- install_remote_script and remote_script_status tools, so Claude can set
  up the Live side itself; connection errors point the model at them

## [0.1.0] - 2026-08-04

Initial release.

- live_set resolves object-valued properties: routing targets (e.g. a
  compressor's sidechain input) by index or display name, and any LOM
  object via value_path
- Numeric values that arrive as strings parse as numbers everywhere
  instead of failing at Live's C++ boundary
- Browser output is paged and search results capped, staying under MCP
  clients' 1MB tool-result limit

- Remote script bridge: threadless tick-polled TCP server inside Live,
  length-prefixed JSON protocol, localhost only
- Generic Live Object Model access: live_get, live_set, live_call,
  live_describe on any LOM path
- Transport, song settings, and cue points
- Track create/delete/duplicate, properties, and routing
- Scenes: create/delete/duplicate/fire
- Session and arrangement clips: create/delete/fire, properties, timeline
  placement
- MIDI note read/add/update/remove with stable note IDs (Live 11+ APIs)
- Mixer: volume, pan, sends, crossfader
- Devices: listing with rack chains and drum pads, parameter get/set
- Clip automation envelopes: write, read, clear
- Browser: navigate, search, load by URI
- Change-event feed: subscribe to listenable properties, poll by cursor
- Installer script, unit suite against a fake LOM, opt-in integration suite
  against a running Live
