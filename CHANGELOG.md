# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [SemVer](https://semver.org/).

## [Unreleased]

### Fixed

- Continuous device parameters can be set again: numeric values that
  arrive as strings ("0.32") now parse as numbers instead of failing the
  quantized-option match; parameter indexes as strings ("3") also work
- live_set and every batched property write coerce stringified numbers
  as well, instead of letting them fail at Live's C++ boundary
- Browser results no longer blow past MCP clients' 1MB tool-result limit:
  browse output is paged (offset/limit, 500 max) and search results cap
  at 100
- README and installer now spell out that the MCP config's --directory is
  the cloned repo path; the installer prints a filled-in config snippet

## [0.1.0] - 2026-08-04

Initial release.

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
