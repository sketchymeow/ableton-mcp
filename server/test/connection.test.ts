import net from "node:net";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { AbletonConnection, BridgeError } from "../src/connection.js";
import { encode, FrameDecoder } from "../src/protocol.js";

type Handler = (message: {
  id: number;
  command: string;
  params: Record<string, unknown>;
}) => Record<string, unknown> | undefined;

/** Minimal stand-in for the remote script's BridgeServer. */
function mockBridge(handler: Handler): Promise<{ port: number; server: net.Server }> {
  const server = net.createServer((socket) => {
    const decoder = new FrameDecoder();
    socket.on("data", (data) => {
      for (const raw of decoder.feed(data)) {
        const message = raw as Parameters<Handler>[0];
        const response = handler(message);
        if (response) socket.write(encode(response));
      }
    });
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () =>
      resolve({ port: (server.address() as net.AddressInfo).port, server }),
    );
  });
}

describe("AbletonConnection", () => {
  let server: net.Server;
  let connection: AbletonConnection;

  afterEach(() => {
    connection?.close();
    server?.close();
  });

  it("round-trips a request", async () => {
    ({ server } = await mockBridge((m) => ({
      id: m.id, status: "ok", result: { echoed: m.params },
    })) as never);
    const { port } = server.address() as net.AddressInfo;
    connection = new AbletonConnection("127.0.0.1", port);
    const result = await connection.request("ping", { x: 1 });
    expect(result).toEqual({ echoed: { x: 1 } });
  });

  it("surfaces bridge errors as BridgeError", async () => {
    ({ server } = await mockBridge((m) => ({
      id: m.id, status: "error",
      error: { type: "unknown_command", message: "nope" },
    })) as never);
    const { port } = server.address() as net.AddressInfo;
    connection = new AbletonConnection("127.0.0.1", port);
    await expect(connection.request("bogus")).rejects.toThrow(BridgeError);
    await expect(connection.request("bogus")).rejects.toThrow("nope");
  });

  it("times out and reports the command name", async () => {
    ({ server } = await mockBridge(() => undefined) as never);
    const { port } = server.address() as net.AddressInfo;
    connection = new AbletonConnection("127.0.0.1", port);
    await expect(connection.request("slow", {}, 100)).rejects.toThrow(
      /timed out waiting for response to 'slow'/,
    );
  });

  it("interleaves concurrent requests by id", async () => {
    ({ server } = await mockBridge((m) => ({
      id: m.id, status: "ok", result: m.params.n,
    })) as never);
    const { port } = server.address() as net.AddressInfo;
    connection = new AbletonConnection("127.0.0.1", port);
    const results = await Promise.all(
      [1, 2, 3, 4, 5].map((n) => connection.request("echo", { n })),
    );
    expect(results).toEqual([1, 2, 3, 4, 5]);
  });

  it("hints about install when nothing is listening", async () => {
    connection = new AbletonConnection("127.0.0.1", 1);
    await expect(connection.request("ping")).rejects.toThrow(
      /install_remote_script/,
    );
  });
});
