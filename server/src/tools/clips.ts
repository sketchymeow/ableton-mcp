// Clip CRUD, firing, properties, and arrangement placement.

import * as z from "zod";
import { bridge, compact, type Registrar } from "./helpers.js";

const location = z.enum(["session", "arrangement"]).default("session");

export function clipRef(args: {
  track_index: number;
  scene_index?: number;
  clip_index?: number;
  location?: string;
}): Record<string, unknown> {
  const loc = args.location ?? "session";
  return loc === "session"
    ? { track_index: args.track_index, location: loc, scene_index: args.scene_index ?? -1 }
    : { track_index: args.track_index, location: loc, clip_index: args.clip_index ?? -1 };
}

export const register: Registrar = (server) => {
  server.registerTool(
    "clip_slot",
    {
      description:
        "Work with a session clip slot: create an empty MIDI clip (length " +
        "in beats), delete the clip, or fire/stop it. Firing respects " +
        "launch quantization.",
      inputSchema: z.object({
        action: z.enum(["create", "delete", "fire", "stop"]),
        track_index: z.number().int(),
        scene_index: z.number().int(),
        length: z.number().default(4.0),
      }),
    },
    async ({ action, track_index, scene_index, length }) => {
      const params: Record<string, unknown> = { track_index, scene_index };
      if (action === "create") params.length = length;
      return bridge(`${action}_clip`, params);
    },
  );

  server.registerTool(
    "get_clip",
    {
      description:
        "Get a clip's properties: loop points, markers, launch settings, " +
        "playback state, and (for audio clips) gain/pitch/warp settings. " +
        "Use scene_index for session clips, clip_index for arrangement clips.",
      inputSchema: z.object({
        track_index: z.number().int(),
        scene_index: z.number().int().default(-1),
        location,
        clip_index: z.number().int().default(-1),
      }),
    },
    async (args) => bridge("get_clip", clipRef(args)),
  );

  server.registerTool(
    "set_clip",
    {
      description:
        "Set clip properties in one call. Only the arguments you pass are " +
        'changed. Times are in beats; color is "#RRGGBB"; gain/pitch/warp ' +
        "apply to audio clips only.",
      inputSchema: z.object({
        track_index: z.number().int(),
        scene_index: z.number().int().default(-1),
        location,
        clip_index: z.number().int().default(-1),
        name: z.string().optional(),
        color: z.string().optional(),
        looping: z.boolean().optional(),
        loop_start: z.number().optional(),
        loop_end: z.number().optional(),
        start_marker: z.number().optional(),
        end_marker: z.number().optional(),
        launch_mode: z.number().int().optional(),
        launch_quantization: z.number().int().optional(),
        legato: z.boolean().optional(),
        muted: z.boolean().optional(),
        gain: z.number().optional(),
        pitch_coarse: z.number().int().optional(),
        pitch_fine: z.number().optional(),
        warping: z.boolean().optional(),
        warp_mode: z.number().int().optional(),
      }),
    },
    async ({ track_index, scene_index, location: loc, clip_index, ...props }) =>
      bridge("set_clip", {
        ...clipRef({ track_index, scene_index, clip_index, location: loc }),
        ...compact(props),
      }),
  );

  server.registerTool(
    "arrangement_clips",
    {
      description: "List a track's arrangement clips with their timeline positions.",
      inputSchema: z.object({ track_index: z.number().int() }),
    },
    async (args) => bridge("get_arrangement_clips", args),
  );

  server.registerTool(
    "clip_to_arrangement",
    {
      description:
        "Copy a session clip onto the arrangement timeline at the given " +
        "time (in beats). This is how you build a song structure from " +
        "session clips.",
      inputSchema: z.object({
        track_index: z.number().int(),
        scene_index: z.number().int(),
        time: z.number(),
      }),
    },
    async (args) => bridge("clip_to_arrangement", args),
  );
};
