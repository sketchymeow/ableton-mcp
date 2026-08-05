// Clip automation envelopes.

import * as z from "zod";
import { clipRef } from "./clips.js";
import { bridge, compact, type Registrar } from "./helpers.js";

const location = z.enum(["session", "arrangement"]).default("session");
const mixerParam = z.enum(["volume", "panning", "cue_volume", "crossfader", "send"]);

const targetArgs = {
  device_index: z.number().int().optional(),
  parameter: z.union([z.number().int(), z.string()]).optional(),
  mixer_parameter: mixerParam.optional(),
  send_index: z.number().int().optional(),
};

function targetParams(args: {
  device_index?: number;
  parameter?: number | string;
  mixer_parameter?: string;
  send_index?: number;
}): Record<string, unknown> {
  const params: Record<string, unknown> = {};
  if (args.device_index !== undefined) {
    params.device_index = args.device_index;
    params.parameter = args.parameter;
  }
  if (args.mixer_parameter !== undefined) {
    params.mixer_parameter = args.mixer_parameter;
    if (args.send_index !== undefined) params.send_index = args.send_index;
  }
  return params;
}

export const register: Registrar = (server) => {
  server.registerTool(
    "write_automation",
    {
      description:
        "Write an automation envelope into a clip - filter sweeps, volume " +
        "ramps, etc. Target a device parameter (device_index + parameter) " +
        "or a mixer parameter (mixer_parameter, with send_index for " +
        "sends). Each point is {time, value} in beats/parameter units; " +
        "optional length holds the value flat for that many beats. Set " +
        "clear_first to replace the existing envelope.",
      inputSchema: z.object({
        track_index: z.number().int(),
        points: z
          .array(
            z.object({
              time: z.number(),
              value: z.number(),
              length: z.number().optional(),
            }),
          )
          .min(1),
        scene_index: z.number().int().default(-1),
        location,
        clip_index: z.number().int().default(-1),
        ...targetArgs,
        clear_first: z.boolean().default(false),
      }),
    },
    async ({ track_index, points, scene_index, location: loc, clip_index,
             clear_first, ...target }) =>
      bridge("write_automation", {
        ...clipRef({ track_index, scene_index, clip_index, location: loc }),
        ...targetParams(target),
        points: points.map((point) => compact(point)),
        clear_first,
      }),
  );

  server.registerTool(
    "read_automation",
    {
      description:
        "Read an automation envelope's values. Pass times (in beats) for " +
        "exact points, or let it sample the clip evenly (samples points). " +
        "has_envelope is false if the parameter has no automation.",
      inputSchema: z.object({
        track_index: z.number().int(),
        scene_index: z.number().int().default(-1),
        location,
        clip_index: z.number().int().default(-1),
        ...targetArgs,
        times: z.array(z.number()).optional(),
        samples: z.number().int().default(17),
      }),
    },
    async ({ track_index, scene_index, location: loc, clip_index, times,
             samples, ...target }) =>
      bridge("read_automation", {
        ...clipRef({ track_index, scene_index, clip_index, location: loc }),
        ...targetParams(target),
        ...(times !== undefined ? { times } : { samples }),
      }),
  );

  server.registerTool(
    "clear_automation",
    {
      description:
        "Clear automation from a clip: pass a target to clear one " +
        "parameter's envelope, or no target to clear every envelope in " +
        "the clip.",
      inputSchema: z.object({
        track_index: z.number().int(),
        scene_index: z.number().int().default(-1),
        location,
        clip_index: z.number().int().default(-1),
        ...targetArgs,
      }),
    },
    async ({ track_index, scene_index, location: loc, clip_index, ...target }) =>
      bridge("clear_automation", {
        ...clipRef({ track_index, scene_index, clip_index, location: loc }),
        ...targetParams(target),
      }),
  );
};
