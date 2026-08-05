// Scene listing, CRUD, and firing.

import * as z from "zod";
import { bridge, compact, type Registrar } from "./helpers.js";

export const register: Registrar = (server) => {
  server.registerTool(
    "list_scenes",
    {
      description:
        "List all scenes with name, color, tempo (if set), and trigger state.",
      inputSchema: z.object({}),
    },
    async () => bridge("get_scenes"),
  );

  server.registerTool(
    "scene",
    {
      description:
        'Create, delete, duplicate, or fire a scene. "create" with index -1 ' +
        "appends at the end; the other actions need a real index. Firing a " +
        "scene launches every clip in that row.",
      inputSchema: z.object({
        action: z.enum(["create", "delete", "duplicate", "fire"]),
        index: z.number().int().default(-1),
      }),
    },
    async ({ action, index }) => {
      if (action !== "create" && index < 0) {
        throw new Error(`${action} needs a scene index`);
      }
      return bridge(`${action}_scene`, { index });
    },
  );

  server.registerTool(
    "set_scene",
    {
      description:
        "Set scene properties in one call. Only the arguments you pass are " +
        'changed. color is "#RRGGBB".',
      inputSchema: z.object({
        index: z.number().int(),
        name: z.string().optional(),
        color: z.string().optional(),
        tempo: z.number().optional(),
      }),
    },
    async (args) => bridge("set_scene", compact(args)),
  );
};
