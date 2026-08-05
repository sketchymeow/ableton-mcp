// MIDI note editing with stable note IDs.

import * as z from "zod";
import { clipRef } from "./clips.js";
import { bridge, compact, type Registrar } from "./helpers.js";

const location = z.enum(["session", "arrangement"]).default("session");

const noteSpec = z
  .object({
    pitch: z.number().int().min(0).max(127),
    start_time: z.number(),
    duration: z.number(),
    velocity: z.number().optional(),
    mute: z.boolean().optional(),
    probability: z.number().optional(),
    velocity_deviation: z.number().optional(),
    release_velocity: z.number().optional(),
  });

const noteUpdate = z
  .object({
    note_id: z.number().int(),
    pitch: z.number().int().optional(),
    start_time: z.number().optional(),
    duration: z.number().optional(),
    velocity: z.number().optional(),
    mute: z.boolean().optional(),
    probability: z.number().optional(),
    velocity_deviation: z.number().optional(),
    release_velocity: z.number().optional(),
  });

const rangeArgs = {
  from_pitch: z.number().int().optional(),
  pitch_span: z.number().int().optional(),
  from_time: z.number().optional(),
  time_span: z.number().optional(),
};

export const register: Registrar = (server) => {
  server.registerTool(
    "get_notes",
    {
      description:
        "Read the MIDI notes in a clip. Each note has a stable note_id you " +
        "can use with update_notes/remove_notes. Omit the range arguments " +
        "to get every note; pass them to read a pitch/time window (times " +
        "in beats).",
      inputSchema: z.object({
        track_index: z.number().int(),
        scene_index: z.number().int().default(-1),
        location,
        clip_index: z.number().int().default(-1),
        ...rangeArgs,
      }),
    },
    async ({ track_index, scene_index, location: loc, clip_index, ...range }) =>
      bridge("get_notes", {
        ...clipRef({ track_index, scene_index, clip_index, location: loc }),
        ...compact(range),
      }),
  );

  server.registerTool(
    "add_notes",
    {
      description:
        "Add MIDI notes to a clip without touching existing ones. Each " +
        "note needs pitch (0-127), start_time and duration (beats); " +
        "optional velocity (0-127, default 100), mute, probability (0-1), " +
        "velocity_deviation, release_velocity. Returns all notes in the " +
        "clip with their IDs.",
      inputSchema: z.object({
        track_index: z.number().int(),
        notes: z.array(noteSpec).min(1),
        scene_index: z.number().int().default(-1),
        location,
        clip_index: z.number().int().default(-1),
      }),
    },
    async ({ track_index, notes, scene_index, location: loc, clip_index }) =>
      bridge("add_notes", {
        ...clipRef({ track_index, scene_index, clip_index, location: loc }),
        notes,
      }),
  );

  server.registerTool(
    "update_notes",
    {
      description:
        "Modify existing notes by ID. Each entry needs the note_id from " +
        "get_notes plus the fields to change (pitch, start_time, duration, " +
        "velocity, mute, probability, velocity_deviation, release_velocity).",
      inputSchema: z.object({
        track_index: z.number().int(),
        notes: z.array(noteUpdate).min(1),
        scene_index: z.number().int().default(-1),
        location,
        clip_index: z.number().int().default(-1),
      }),
    },
    async ({ track_index, notes, scene_index, location: loc, clip_index }) =>
      bridge("update_notes", {
        ...clipRef({ track_index, scene_index, clip_index, location: loc }),
        notes: notes.map((note) => compact(note)),
      }),
  );

  server.registerTool(
    "remove_notes",
    {
      description:
        "Remove notes from a clip: pass note_ids for specific notes, or a " +
        "pitch/time range. With neither, every note in the clip is removed.",
      inputSchema: z.object({
        track_index: z.number().int(),
        scene_index: z.number().int().default(-1),
        location,
        clip_index: z.number().int().default(-1),
        note_ids: z.array(z.number().int()).optional(),
        ...rangeArgs,
      }),
    },
    async ({ track_index, scene_index, location: loc, clip_index, ...rest }) =>
      bridge("remove_notes", {
        ...clipRef({ track_index, scene_index, clip_index, location: loc }),
        ...compact(rest),
      }),
  );
};
