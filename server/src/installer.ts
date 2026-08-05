// Install the AbletonMCP remote script into Live's User Library.

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

export class InstallError extends Error {}

const here = path.dirname(fileURLToPath(import.meta.url));

export function remoteScriptSource(): string {
  // dist/index.js and the mcpb bundle both keep remote_script one level up;
  // running from src/ (tsx) it's two levels up at the repo root.
  const candidates = [
    path.join(here, "..", "remote_script", "AbletonMCP"),
    path.join(here, "..", "..", "remote_script", "AbletonMCP"),
  ];
  for (const candidate of candidates) {
    if (fs.existsSync(path.join(candidate, "__init__.py"))) {
      return candidate;
    }
  }
  throw new InstallError("could not locate the bundled remote script");
}

export function defaultDest(): string | null {
  const home = os.homedir();
  if (process.platform === "darwin") {
    return path.join(home, "Music", "Ableton", "User Library", "Remote Scripts");
  }
  if (process.platform === "win32") {
    return path.join(home, "Documents", "Ableton", "User Library", "Remote Scripts");
  }
  return null;
}

export interface InstallResult {
  installed_to: string;
  mode: "copy" | "symlink";
  replaced_existing: boolean;
  next_steps: string[];
}

export function install(options: { dest?: string; symlink?: boolean } = {}): InstallResult {
  const source = remoteScriptSource();
  const dest = options.dest ?? defaultDest();
  if (!dest) {
    throw new InstallError(
      "could not guess the Remote Scripts folder on this OS; pass an explicit destination",
    );
  }
  fs.mkdirSync(dest, { recursive: true });
  const target = path.join(dest, "AbletonMCP");
  const replaced = fs.existsSync(target);
  fs.rmSync(target, { recursive: true, force: true });

  if (options.symlink) {
    fs.symlinkSync(source, target, "dir");
  } else {
    fs.cpSync(source, target, {
      recursive: true,
      filter: (src) => {
        const base = path.basename(src);
        return base !== "__pycache__" && base !== "logs" && !base.endsWith(".pyc");
      },
    });
  }
  return {
    installed_to: target,
    mode: options.symlink ? "symlink" : "copy",
    replaced_existing: replaced,
    next_steps: [
      "Restart Ableton Live.",
      "Settings > Link, Tempo & MIDI > Control Surface > AbletonMCP.",
      "Look for 'AbletonMCP: listening on 127.0.0.1:9877' in Live's status bar.",
    ],
  };
}
