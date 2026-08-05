// Live browser: navigate, search, load.

import * as z from "zod";
import { bridge, type Registrar } from "./helpers.js";

const root = z.enum([
  "instruments", "sounds", "drums", "audio_effects", "midi_effects",
  "plugins", "samples", "packs", "user_library", "current_project",
]);
const trackType = z.enum(["track", "return", "master"]).default("track");

export const register: Registrar = (server) => {
  server.registerTool(
    "browse",
    {
      description:
        "List one level of Live's browser. path drills down from the root " +
        'by item name or index (e.g. ["Operator"] lists Operator\'s ' +
        "presets). Loadable items have a uri for load_browser_item. Output " +
        "is paged (max 500 per call); check total and pass offset for the " +
        "rest.",
      inputSchema: z.object({
        root: root.default("instruments"),
        path: z.array(z.union([z.string(), z.number().int()])).default([]),
        offset: z.number().int().default(0),
        limit: z.number().int().default(200),
      }),
    },
    async (args) => bridge("browse", args, 30_000),
  );

  server.registerTool(
    "search_browser",
    {
      description:
        "Search the browser by name for loadable devices, presets, and " +
        "sounds. Defaults to instruments/sounds/drums/effects/plugins; " +
        "pass roots to search elsewhere (e.g. samples). Results cap at 100 " +
        "and the sweep is budgeted, so truncated=true means narrow the " +
        "query or browse directly.",
      inputSchema: z.object({
        query: z.string(),
        roots: z.array(root).optional(),
        max_results: z.number().int().default(25),
      }),
    },
    async ({ query, roots, max_results }) =>
      bridge(
        "search_browser",
        { query, max_results, ...(roots !== undefined ? { roots } : {}) },
        45_000,
      ),
  );

  server.registerTool(
    "load_browser_item",
    {
      description:
        "Load a browser item by uri (from browse/search_browser) - " +
        "instruments and effects go onto the given track (or the currently " +
        "selected one if track_index is omitted).",
      inputSchema: z.object({
        uri: z.string(),
        track_index: z.number().int().optional(),
        track_type: trackType,
      }),
    },
    async ({ uri, track_index, track_type }) =>
      bridge(
        "load_browser_item",
        { uri, track_type, ...(track_index !== undefined ? { track_index } : {}) },
        60_000,
      ),
  );
};
