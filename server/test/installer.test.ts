import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { install, remoteScriptSource } from "../src/installer.js";

describe("installer", () => {
  let dest: string;

  beforeEach(() => {
    dest = fs.mkdtempSync(path.join(os.tmpdir(), "abletonmcp-test-"));
  });

  afterEach(() => {
    fs.rmSync(dest, { recursive: true, force: true });
  });

  it("finds the remote script in the checkout", () => {
    expect(fs.existsSync(path.join(remoteScriptSource(), "surface.py"))).toBe(true);
  });

  it("copies the remote script", () => {
    const result = install({ dest });
    expect(result.mode).toBe("copy");
    expect(result.replaced_existing).toBe(false);
    const target = path.join(dest, "AbletonMCP");
    expect(fs.existsSync(path.join(target, "core", "protocol.py"))).toBe(true);
    expect(fs.existsSync(path.join(target, "__pycache__"))).toBe(false);
  });

  it("replaces an existing install", () => {
    install({ dest });
    const marker = path.join(dest, "AbletonMCP", "stale.txt");
    fs.writeFileSync(marker, "old");
    const result = install({ dest });
    expect(result.replaced_existing).toBe(true);
    expect(fs.existsSync(marker)).toBe(false);
  });

  it("symlinks when asked", () => {
    const result = install({ dest, symlink: true });
    expect(result.mode).toBe("symlink");
    const target = path.join(dest, "AbletonMCP");
    expect(fs.lstatSync(target).isSymbolicLink()).toBe(true);
  });
});
