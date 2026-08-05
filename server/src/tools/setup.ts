// First-run setup: install the remote script from inside the MCP server.

import fs from "node:fs";
import path from "node:path";
import * as z from "zod";
import { defaultDest, install, InstallError } from "../installer.js";
import { json, type Registrar } from "./helpers.js";

export const register: Registrar = (server) => {
  server.registerTool(
    "install_remote_script",
    {
      description:
        "Install the AbletonMCP control surface into Ableton Live's User " +
        "Library. Call this when ping can't reach Live and the user hasn't " +
        "set the remote script up yet (or needs it updated). The user must " +
        "restart Live afterwards - tell them the next_steps.",
      inputSchema: z.object({ dest: z.string().optional() }),
    },
    async ({ dest }) => {
      try {
        return json(install({ dest }));
      } catch (error) {
        if (error instanceof InstallError) {
          return json({ error: error.message });
        }
        throw error;
      }
    },
  );

  server.registerTool(
    "remote_script_status",
    {
      description:
        "Check whether the AbletonMCP remote script is installed in Live's " +
        "User Library (this says nothing about whether Live is running - " +
        "use ping for that).",
      inputSchema: z.object({}),
    },
    async () => {
      const dest = defaultDest();
      if (!dest) {
        return json({
          installed: false,
          reason: "unsupported OS; pass an explicit dest to install_remote_script",
        });
      }
      const target = path.join(dest, "AbletonMCP");
      let isSymlink = false;
      try {
        isSymlink = fs.lstatSync(target).isSymbolicLink();
      } catch {
        // not installed
      }
      return json({
        installed: fs.existsSync(target),
        path: target,
        is_symlink: isSymlink,
      });
    },
  );
};
