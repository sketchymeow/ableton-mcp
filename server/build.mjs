// Build dist/index.js (single-file server) and, with --mcpb, the Claude
// Desktop bundle. One bundle works on every platform: no native binary,
// Claude Desktop runs it with its own Node runtime.

import { execFileSync, spawnSync } from "node:child_process";
import esbuild from "esbuild";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.join(here, "..");
const pkg = JSON.parse(fs.readFileSync(path.join(here, "package.json"), "utf-8"));

await esbuild.build({
  entryPoints: [path.join(here, "src", "index.ts")],
  bundle: true,
  platform: "node",
  format: "esm",
  target: "node18",
  outfile: path.join(here, "dist", "index.js"),
  banner: {
    js: '#!/usr/bin/env node\nimport { createRequire } from "node:module";\nconst require = createRequire(import.meta.url);',
  },
});
fs.chmodSync(path.join(here, "dist", "index.js"), 0o755);

// The installer looks for remote_script next to dist/ in packaged layouts.
fs.rmSync(path.join(here, "remote_script"), { recursive: true, force: true });
fs.cpSync(
  path.join(repo, "remote_script", "AbletonMCP"),
  path.join(here, "remote_script", "AbletonMCP"),
  {
    recursive: true,
    filter: (src) => {
      const base = path.basename(src);
      return base !== "__pycache__" && base !== "logs" && !base.endsWith(".pyc");
    },
  },
);

smokeTest();
console.log("built dist/index.js");

if (process.argv.includes("--mcpb")) {
  const stage = path.join(here, "dist", "mcpb-stage");
  fs.rmSync(stage, { recursive: true, force: true });
  fs.mkdirSync(path.join(stage, "server"), { recursive: true });
  fs.copyFileSync(
    path.join(here, "dist", "index.js"),
    path.join(stage, "server", "index.js"),
  );
  fs.cpSync(path.join(here, "remote_script"), path.join(stage, "remote_script"), {
    recursive: true,
  });
  fs.writeFileSync(
    path.join(stage, "manifest.json"),
    JSON.stringify(manifest(), null, 2),
  );
  const out = path.join(here, "dist", "ableton-mcp.mcpb");
  fs.rmSync(out, { force: true });
  execFileSync("npx", ["--no-install", "mcpb", "pack", stage, out], {
    stdio: "inherit",
  });
  console.log(`built ${out} (${Math.round(fs.statSync(out).size / 1024)} KB)`);
}

function manifest() {
  return {
    manifest_version: "0.2",
    name: "ableton-mcp",
    display_name: "Ableton Live",
    version: pkg.version,
    description:
      "Control Ableton Live: tracks, clips, MIDI notes, devices, mixing, " +
      "automation, and the browser.",
    author: { name: "Sketchy Meow" },
    repository: { type: "git", url: "https://github.com/sketchymeow/ableton-mcp" },
    server: {
      type: "node",
      entry_point: "server/index.js",
      mcp_config: {
        command: "node",
        args: ["${__dirname}/server/index.js"],
      },
    },
  };
}

function smokeTest() {
  const request =
    JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method: "initialize",
      params: {
        protocolVersion: "2025-06-18",
        capabilities: {},
        clientInfo: { name: "smoke", version: "0" },
      },
    }) + "\n";
  const proc = spawnSync("node", [path.join(here, "dist", "index.js")], {
    input: request,
    timeout: 30_000,
    encoding: "utf-8",
  });
  if (!proc.stdout?.includes('"serverInfo"')) {
    console.error(proc.stderr);
    throw new Error("smoke test failed: no initialize response");
  }
  console.log("smoke test passed: bundle answers MCP initialize");
}
