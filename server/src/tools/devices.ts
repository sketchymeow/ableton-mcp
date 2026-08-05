// Device listing and parameter control.

import * as z from "zod";
import { bridge, type Registrar } from "./helpers.js";

const trackType = z.enum(["track", "return", "master"]).default("track");

export const register: Registrar = (server) => {
  server.registerTool(
    "list_devices",
    {
      description:
        "List a track's devices, including rack chains and drum pads. Each " +
        "device has a LOM path usable with live_get/live_set/live_call for " +
        "anything the curated tools don't cover (e.g. devices nested " +
        "inside racks).",
      inputSchema: z.object({
        track_index: z.number().int().default(0),
        track_type: trackType,
      }),
    },
    async (args) => bridge("get_devices", args),
  );

  server.registerTool(
    "device_parameters",
    {
      description:
        "List a device's parameters: name, value, range, display string, " +
        "and (for switches/menus) the list of valid options.",
      inputSchema: z.object({
        track_index: z.number().int(),
        device_index: z.number().int(),
        track_type: trackType,
      }),
    },
    async (args) => bridge("get_device_parameters", args),
  );

  server.registerTool(
    "set_device_parameter",
    {
      description:
        "Set a device parameter by index or name. Pass a number for " +
        "continuous parameters (clamped to the parameter's range) or an " +
        'option name (e.g. "High") for quantized ones. "Device On" with ' +
        "0/1 turns the device off/on.",
      inputSchema: z.object({
        track_index: z.number().int(),
        device_index: z.number().int(),
        parameter: z.union([z.number().int(), z.string()]),
        value: z.union([z.number(), z.string()]),
        track_type: trackType,
      }),
    },
    async (args) => bridge("set_device_parameter", args),
  );

  server.registerTool(
    "delete_device",
    {
      description: "Remove a device from a track.",
      inputSchema: z.object({
        track_index: z.number().int(),
        device_index: z.number().int(),
        track_type: trackType,
      }),
    },
    async (args) => bridge("delete_device", args),
  );
};
