// Track listing, CRUD, properties, and routing.

import * as z from "zod";
import { bridge, compact, type Registrar } from "./helpers.js";

const trackType = z.enum(["track", "return", "master"]).default("track");

export const register: Registrar = (server) => {
  server.registerTool(
    "list_tracks",
    {
      description:
        "List all tracks (regular, return, and master) with type, name, " +
        "color, mute/solo/arm state, devices, and clip counts.",
      inputSchema: z.object({}),
    },
    async () => bridge("get_tracks"),
  );

  server.registerTool(
    "get_track",
    {
      description:
        "Get one track in detail: summary plus monitoring, fold state, clip " +
        "slots, and current/available input and output routing.",
      inputSchema: z.object({
        track_index: z.number().int(),
        track_type: trackType,
      }),
    },
    async (args) => bridge("get_track", args),
  );

  server.registerTool(
    "create_track",
    {
      description:
        "Create a track. index -1 appends at the end (return tracks always " +
        "append). Returns the new track's summary including its index.",
      inputSchema: z.object({
        type: z.enum(["midi", "audio", "return"]).default("midi"),
        index: z.number().int().default(-1),
      }),
    },
    async (args) => bridge("create_track", args),
  );

  server.registerTool(
    "delete_track",
    {
      description:
        "Delete a track or return track. The master track cannot be deleted.",
      inputSchema: z.object({
        track_index: z.number().int(),
        track_type: trackType,
      }),
    },
    async (args) => bridge("delete_track", args),
  );

  server.registerTool(
    "duplicate_track",
    {
      description:
        "Duplicate a regular track, including its devices and clips. The " +
        "copy lands right after the original.",
      inputSchema: z.object({ track_index: z.number().int() }),
    },
    async (args) => bridge("duplicate_track", args),
  );

  server.registerTool(
    "set_track",
    {
      description:
        "Set track properties in one call. Only the arguments you pass are " +
        'changed. color is "#RRGGBB".',
      inputSchema: z.object({
        track_index: z.number().int(),
        track_type: trackType,
        name: z.string().optional(),
        color: z.string().optional(),
        arm: z.boolean().optional(),
        mute: z.boolean().optional(),
        solo: z.boolean().optional(),
        monitoring: z.enum(["in", "auto", "off"]).optional(),
        fold_state: z.number().int().optional(),
      }),
    },
    async (args) => bridge("set_track", compact(args)),
  );

  server.registerTool(
    "track_routing",
    {
      description:
        "Get or set track routing. With no routing arguments this returns " +
        "the current and available options; pass display names from the " +
        "available lists to change routing.",
      inputSchema: z.object({
        track_index: z.number().int(),
        track_type: trackType,
        input_type: z.string().optional(),
        input_channel: z.string().optional(),
        output_type: z.string().optional(),
        output_channel: z.string().optional(),
      }),
    },
    async ({ track_index, track_type, ...changes }) => {
      const set = compact(changes);
      const base = { track_index, track_type };
      return Object.keys(set).length
        ? bridge("set_track_routing", { ...base, ...set })
        : bridge("get_track_routing", base);
    },
  );
};
