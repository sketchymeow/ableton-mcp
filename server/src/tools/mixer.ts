// Mixer control: volume, pan, sends, crossfader.

import * as z from "zod";
import { bridge, compact, type Registrar } from "./helpers.js";

const trackType = z.enum(["track", "return", "master"]).default("track");

export const register: Registrar = (server) => {
  server.registerTool(
    "get_mixer",
    {
      description:
        "Get a track's mixer state: volume, pan, sends (with the return " +
        "track each one feeds), and crossfade assignment. Values come with " +
        'display strings (e.g. "0.0 dB").',
      inputSchema: z.object({
        track_index: z.number().int().default(0),
        track_type: trackType,
      }),
    },
    async (args) => bridge("get_mixer", args),
  );

  server.registerTool(
    "set_mixer",
    {
      description:
        "Set mixer values in one call. volume is 0..1 (0.85 = 0 dB), " +
        "panning is -1..1. cue_volume and crossfader exist on the master " +
        "track only. Returns the updated mixer state with display strings.",
      inputSchema: z.object({
        track_index: z.number().int().default(0),
        track_type: trackType,
        volume: z.number().optional(),
        panning: z.number().optional(),
        crossfade_assign: z.enum(["A", "none", "B"]).optional(),
        cue_volume: z.number().optional(),
        crossfader: z.number().optional(),
      }),
    },
    async (args) => bridge("set_mixer", compact(args)),
  );

  server.registerTool(
    "set_send",
    {
      description:
        "Set a send level (0..1). send_index matches the return track " +
        "order from get_mixer/list_tracks.",
      inputSchema: z.object({
        track_index: z.number().int(),
        send_index: z.number().int(),
        value: z.number(),
        track_type: trackType,
      }),
    },
    async (args) => bridge("set_send", args),
  );
};
