// End-to-end through the real server: stdio JSON-RPC in, bridge commands
// out. A mock bridge records what each tool actually sends, so tool->command
// mapping bugs (the class of bug a port introduces) fail here.

import { type ChildProcess, spawn } from "node:child_process";
import net from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { encode, FrameDecoder } from "../src/protocol.js";

const here = path.dirname(fileURLToPath(import.meta.url));

interface BridgeCall {
  command: string;
  params: Record<string, unknown>;
}

const calls: BridgeCall[] = [];
let bridge: net.Server;
let server: ChildProcess;
let nextId = 10;
const pending = new Map<number, (result: unknown) => void>();
let stdoutBuf = "";

// Canned bridge results for commands whose tools post-process the response.
const results: Record<string, unknown> = {
  get_song_status: { tempo: 120 },
  get_cue_points: { cue_points: [] },
};

function rpc(method: string, params?: unknown): Promise<unknown> {
  const id = nextId++;
  server.stdin!.write(JSON.stringify({ jsonrpc: "2.0", id, method, params }) + "\n");
  return new Promise((resolve) => pending.set(id, resolve));
}

async function callTool(
  name: string,
  args: Record<string, unknown>,
): Promise<{ calls: BridgeCall[]; result: unknown }> {
  calls.length = 0;
  const result = await rpc("tools/call", { name, arguments: args });
  return { calls: [...calls], result };
}

beforeAll(async () => {
  bridge = net.createServer((socket) => {
    const decoder = new FrameDecoder();
    socket.on("data", (data) => {
      for (const raw of decoder.feed(data)) {
        const message = raw as { id: number } & BridgeCall;
        calls.push({ command: message.command, params: message.params });
        socket.write(
          encode({
            id: message.id,
            status: "ok",
            result: results[message.command] ?? { ok: true },
          }),
        );
      }
    });
  });
  const port = await new Promise<number>((resolve) => {
    bridge.listen(0, "127.0.0.1", () =>
      resolve((bridge.address() as net.AddressInfo).port),
    );
  });

  server = spawn(
    process.execPath,
    ["--import", "tsx", path.join(here, "..", "src", "index.ts")],
    {
      env: { ...process.env, ABLETON_MCP_PORT: String(port) },
      stdio: ["pipe", "pipe", "inherit"],
    },
  );
  server.stdout!.on("data", (data: Buffer) => {
    stdoutBuf += data.toString();
    let newline;
    while ((newline = stdoutBuf.indexOf("\n")) >= 0) {
      const line = stdoutBuf.slice(0, newline);
      stdoutBuf = stdoutBuf.slice(newline + 1);
      if (!line.trim()) continue;
      const message = JSON.parse(line) as { id?: number; result?: unknown };
      if (message.id !== undefined && pending.has(message.id)) {
        pending.get(message.id)!(message.result);
        pending.delete(message.id);
      }
    }
  });

  await rpc("initialize", {
    protocolVersion: "2025-06-18",
    capabilities: {},
    clientInfo: { name: "tools-test", version: "0" },
  });
  server.stdin!.write(
    JSON.stringify({ jsonrpc: "2.0", method: "notifications/initialized" }) + "\n",
  );
}, 30_000);

afterAll(() => {
  server?.kill();
  bridge?.close();
});

describe("tool -> bridge command mapping", () => {
  it("ping maps straight through", async () => {
    const { calls } = await callTool("ping", {});
    expect(calls).toEqual([{ command: "ping", params: {} }]);
  });

  // Regression: numeric values arriving as strings must pass through
  // untouched (the bridge does the coercion — "0.32" broke every
  // continuous parameter before).
  it("set_device_parameter passes stringified numbers through", async () => {
    const { calls } = await callTool("set_device_parameter", {
      track_index: 0, device_index: 1, parameter: "Osc-B Level", value: "0.32",
    });
    expect(calls[0].command).toBe("set_device_parameter");
    expect(calls[0].params.value).toBe("0.32");
    expect(calls[0].params.parameter).toBe("Osc-B Level");
  });

  // Regression: live_set needs both scalar and value_path forms (sidechain
  // routing / selected_drum_pad were unsettable before value_path).
  it("live_set sends value or value_path, never both", async () => {
    let { calls } = await callTool("live_set", {
      path: "song", property: "tempo", value: 90,
    });
    expect(calls[0].params).toEqual({ path: "song", property: "tempo", value: 90 });

    ({ calls } = await callTool("live_set", {
      path: "song.view",
      property: "selected_track",
      value_path: "song.tracks[1]",
    }));
    expect(calls[0].params).toEqual({
      path: "song.view",
      property: "selected_track",
      value_path: "song.tracks[1]",
    });
  });

  // Regression: browser results blew past the 1MB tool-result cap; the
  // paging/limit params have to actually reach the bridge.
  it("browse forwards paging and search forwards max_results", async () => {
    let { calls } = await callTool("browse", {
      root: "samples", offset: 200, limit: 100,
    });
    expect(calls[0].params).toEqual({
      root: "samples", path: [], offset: 200, limit: 100,
    });

    ({ calls } = await callTool("search_browser", { query: "kick" }));
    expect(calls[0].params).toEqual({ query: "kick", max_results: 25 });
  });

  it("browse reaches Places via the user_folders root", async () => {
    const { calls } = await callTool("browse", { root: "user_folders" });
    expect(calls[0].params).toMatchObject({ root: "user_folders" });
  });

  it("clip tools address session and arrangement clips correctly", async () => {
    let { calls } = await callTool("get_clip", {
      track_index: 2, scene_index: 3,
    });
    expect(calls[0].params).toEqual({
      track_index: 2, location: "session", scene_index: 3,
    });

    ({ calls } = await callTool("get_clip", {
      track_index: 2, location: "arrangement", clip_index: 5,
    }));
    expect(calls[0].params).toEqual({
      track_index: 2, location: "arrangement", clip_index: 5,
    });
  });

  it("add_notes keeps note fields intact", async () => {
    const { calls } = await callTool("add_notes", {
      track_index: 0,
      scene_index: 0,
      notes: [{ pitch: 60, start_time: 0, duration: 1, velocity: 80 }],
    });
    expect(calls[0].command).toBe("add_notes");
    expect(calls[0].params.notes).toEqual([
      { pitch: 60, start_time: 0, duration: 1, velocity: 80 },
    ]);
  });

  it("update_notes drops undefined optionals", async () => {
    const { calls } = await callTool("update_notes", {
      track_index: 0,
      scene_index: 0,
      notes: [{ note_id: 7, velocity: 40 }],
    });
    expect(calls[0].params.notes).toEqual([{ note_id: 7, velocity: 40 }]);
  });

  it("automation targets mixer and device parameters", async () => {
    let { calls } = await callTool("write_automation", {
      track_index: 0,
      scene_index: 0,
      mixer_parameter: "send",
      send_index: 1,
      points: [{ time: 0, value: 0.5 }],
    });
    expect(calls[0].params).toMatchObject({
      mixer_parameter: "send", send_index: 1,
      points: [{ time: 0, value: 0.5 }], clear_first: false,
    });
    expect(calls[0].params).not.toHaveProperty("device_index");

    ({ calls } = await callTool("read_automation", {
      track_index: 0, scene_index: 0, device_index: 2, parameter: "Dry/Wet",
      times: [0, 1],
    }));
    expect(calls[0].params).toMatchObject({
      device_index: 2, parameter: "Dry/Wet", times: [0, 1],
    });
    expect(calls[0].params).not.toHaveProperty("samples");
  });

  it("track_routing reads without args and writes with them", async () => {
    let { calls } = await callTool("track_routing", { track_index: 0 });
    expect(calls[0].command).toBe("get_track_routing");

    ({ calls } = await callTool("track_routing", {
      track_index: 0, input_type: "Resampling",
    }));
    expect(calls[0].command).toBe("set_track_routing");
    expect(calls[0].params.input_type).toBe("Resampling");
  });

  it("set_track drops unset optionals", async () => {
    const { calls } = await callTool("set_track", {
      track_index: 1, name: "Bass",
    });
    expect(calls[0].params).toEqual({
      track_index: 1, track_type: "track", name: "Bass",
    });
  });

  it("transport composes position + action + status", async () => {
    const { calls } = await callTool("transport", {
      action: "play", position: 8,
    });
    expect(calls.map((c) => c.command)).toEqual([
      "set_property", "call_method", "get_song_status",
    ]);
    expect(calls[0].params).toEqual({
      path: "song", property: "current_song_time", value: 8,
    });
    expect(calls[1].params).toEqual({ path: "song", method: "start_playing" });
  });
});
