// Change feed: subscribe to Live properties and poll for changes.

import * as z from "zod";
import { bridge, compact, type Registrar } from "./helpers.js";

export const register: Registrar = (server) => {
  server.registerTool(
    "live_subscribe",
    {
      description:
        "Subscribe to changes of a Live Object Model property (e.g. " +
        'path="song" property="tempo", or path="song.tracks[0]" ' +
        'property="playing_slot_index"). Changes accumulate in a buffer ' +
        "you read with live_poll_events. live_describe lists which " +
        "properties are listenable.",
      inputSchema: z.object({ path: z.string(), property: z.string() }),
    },
    async (args) => bridge("subscribe", args),
  );

  server.registerTool(
    "live_unsubscribe",
    {
      description:
        "Remove one subscription (path + property) or all of them (no " +
        "arguments).",
      inputSchema: z.object({
        path: z.string().optional(),
        property: z.string().optional(),
      }),
    },
    async (args) => bridge("unsubscribe", compact(args)),
  );

  server.registerTool(
    "live_poll_events",
    {
      description:
        "Read buffered change events past the given cursor. Use last_seq " +
        "from the previous poll as since. Call this before acting on a " +
        "session you haven't touched recently - the user may have changed " +
        "things.",
      inputSchema: z.object({ since: z.number().int().default(0) }),
    },
    async (args) => bridge("poll_events", args),
  );
};
