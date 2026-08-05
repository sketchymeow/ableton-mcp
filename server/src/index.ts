// MCP server exposing Ableton Live over the remote script bridge.

import { McpServer } from "@modelcontextprotocol/server";
import { serveStdio } from "@modelcontextprotocol/server/stdio";
import * as automation from "./tools/automation.js";
import * as browser from "./tools/browser.js";
import * as clips from "./tools/clips.js";
import * as devices from "./tools/devices.js";
import * as events from "./tools/events.js";
import * as mixer from "./tools/mixer.js";
import * as notes from "./tools/notes.js";
import * as raw from "./tools/raw.js";
import * as scenes from "./tools/scenes.js";
import * as setup from "./tools/setup.js";
import * as song from "./tools/song.js";
import * as tracks from "./tools/tracks.js";

export const VERSION = "0.3.0";

export function createServer(): McpServer {
  const server = new McpServer({ name: "ableton-live", version: VERSION });
  for (const module of [
    raw, song, tracks, scenes, clips, notes, mixer, devices, automation,
    browser, events, setup,
  ]) {
    module.register(server);
  }
  return server;
}

serveStdio(() => createServer());
