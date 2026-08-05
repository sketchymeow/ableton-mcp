// Transport, song settings, and cue points.

import * as z from "zod";
import { getConnection } from "../connection.js";
import { bridge, compact, json, type Registrar } from "./helpers.js";

const TRANSPORT_METHODS: Record<string, string> = {
  play: "start_playing",
  stop: "stop_playing",
  continue: "continue_playing",
  stop_all_clips: "stop_all_clips",
  undo: "undo",
  redo: "redo",
  tap_tempo: "tap_tempo",
};

export const register: Registrar = (server) => {
  server.registerTool(
    "song_status",
    {
      description:
        "Get the song state in one call: tempo, time signature, playback, " +
        "loop region, recording state, quantization, and track/scene counts.",
      inputSchema: z.object({}),
    },
    async () => bridge("get_song_status"),
  );

  server.registerTool(
    "transport",
    {
      description:
        'Control playback. "play" restarts from the last start point, ' +
        '"continue" resumes from the current position. Pass position (in ' +
        "beats) to jump there first.",
      inputSchema: z.object({
        action: z.enum([
          "play", "stop", "continue", "stop_all_clips", "undo", "redo",
          "tap_tempo",
        ]),
        position: z.number().optional(),
      }),
    },
    async ({ action, position }) => {
      const conn = getConnection();
      if (position !== undefined) {
        await conn.request("set_property", {
          path: "song", property: "current_song_time", value: position,
        });
      }
      await conn.request("call_method", {
        path: "song", method: TRANSPORT_METHODS[action],
      });
      return json(await conn.request("get_song_status"));
    },
  );

  server.registerTool(
    "set_song",
    {
      description:
        "Set song-level properties in one call. Only the arguments you pass " +
        "are changed. Returns the updated song status.",
      inputSchema: z.object({
        tempo: z.number().optional(),
        signature_numerator: z.number().int().optional(),
        signature_denominator: z.number().int().optional(),
        metronome: z.boolean().optional(),
        loop: z.boolean().optional(),
        loop_start: z.number().optional(),
        loop_length: z.number().optional(),
        record_mode: z.boolean().optional(),
        session_record: z.boolean().optional(),
        clip_trigger_quantization: z.number().int().optional(),
        midi_recording_quantization: z.number().int().optional(),
        groove_amount: z.number().optional(),
      }),
    },
    async (args) => bridge("set_song", compact(args)),
  );

  server.registerTool(
    "cue_points",
    {
      description:
        'Work with arrangement locators. "jump_to" needs the index from ' +
        '"list". "toggle_at_playhead" creates or deletes a locator at the ' +
        "current position.",
      inputSchema: z.object({
        action: z.enum([
          "list", "jump_next", "jump_prev", "jump_to", "toggle_at_playhead",
        ]),
        index: z.number().int().optional(),
      }),
    },
    async ({ action, index }) => {
      const conn = getConnection();
      if (action === "list") {
        return json(await conn.request("get_cue_points"));
      }
      if (action === "jump_to") {
        if (index === undefined) {
          throw new Error("jump_to needs an index; call with action='list' first");
        }
        await conn.request("call_method", {
          path: `song.cue_points[${index}]`, method: "jump",
        });
      } else {
        const method = {
          jump_next: "jump_to_next_cue",
          jump_prev: "jump_to_prev_cue",
          toggle_at_playhead: "set_or_delete_cue",
        }[action];
        await conn.request("call_method", { path: "song", method });
      }
      return json(await conn.request("get_cue_points"));
    },
  );
};
