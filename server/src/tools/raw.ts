// Generic Live Object Model access. Full API coverage, minimal ergonomics.

import * as z from "zod";
import { bridge, type Registrar } from "./helpers.js";

export const register: Registrar = (server) => {
  server.registerTool(
    "ping",
    {
      description:
        "Check the connection to Ableton Live. Returns the Live version if " +
        "reachable. Use this first if other tools are failing.",
      inputSchema: z.object({}),
    },
    async () => bridge("ping"),
  );

  server.registerTool(
    "live_get",
    {
      description:
        "Read a property from any Live Object Model path.\n\n" +
        'Examples: path="song" property="tempo", path="song.tracks[0]" ' +
        'property="name", path="song.tracks[0].devices[0].parameters[3]" ' +
        'property="value". Use live_describe to discover paths and properties.',
      inputSchema: z.object({ path: z.string(), property: z.string() }),
    },
    async ({ path, property }) => bridge("get_property", { path, property }),
  );

  server.registerTool(
    "live_set",
    {
      description:
        "Set a property on any Live Object Model path. Returns the value " +
        "after the write so you can confirm it took (Live clamps " +
        "out-of-range values).\n\nRouting-style properties (ones with an " +
        "available_* sibling, like a compressor's sidechain " +
        "input_routing_type) accept an index or display name and resolve to " +
        "the right object. For other object-valued properties " +
        "(view.selected_track, a drum rack view's selected_drum_pad), pass " +
        "value_path with the LOM path of the object to assign instead of " +
        "value.",
      inputSchema: z.object({
        path: z.string(),
        property: z.string(),
        value: z.union([z.boolean(), z.number(), z.string()]).optional(),
        value_path: z.string().optional(),
      }),
    },
    async ({ path, property, value, value_path }) =>
      bridge(
        "set_property",
        value_path !== undefined
          ? { path, property, value_path }
          : { path, property, value: value ?? null },
      ),
  );

  server.registerTool(
    "live_call",
    {
      description:
        "Call a method on any Live Object Model path.\n\n" +
        'Examples: path="song" method="create_midi_track" args=[-1], ' +
        'path="song" method="start_playing".',
      inputSchema: z.object({
        path: z.string(),
        method: z.string(),
        args: z.array(z.union([z.boolean(), z.number(), z.string()])).optional(),
      }),
    },
    async ({ path, method, args }) =>
      bridge("call_method", { path, method, args: args ?? [] }),
  );

  server.registerTool(
    "live_describe",
    {
      description:
        "Introspect a Live Object Model path: its properties with current " +
        "values, callable methods, and listenable properties. Start at " +
        'path="song" or path="app" and drill down.',
      inputSchema: z.object({ path: z.string() }),
    },
    async ({ path }) => bridge("describe", { path }),
  );
};
