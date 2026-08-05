// TCP client for the AbletonMCP remote script bridge.

import net from "node:net";
import { FrameDecoder, FrameError, encode } from "./protocol.js";

export const DEFAULT_HOST = "127.0.0.1";
export const DEFAULT_PORT = 9877;
const DEFAULT_TIMEOUT_MS = 12_000;
const CONNECT_TIMEOUT_MS = 5_000;

const NOT_RUNNING_HINT =
  "Could not reach Ableton Live on {host}:{port}. Make sure Live is running " +
  "and the AbletonMCP control surface is enabled in Settings > " +
  "Link/Tempo/MIDI. If the remote script was never installed, check with " +
  "remote_script_status and install it with install_remote_script, then " +
  "have the user restart Live.";

export class BridgeError extends Error {
  constructor(public errorType: string, message: string) {
    super(message);
  }
}

class TransportError extends Error {}

interface Pending {
  resolve: (value: unknown) => void;
  reject: (error: Error) => void;
  timer: NodeJS.Timeout;
}

interface Response {
  id?: number;
  status?: string;
  result?: unknown;
  error?: { type?: string; message?: string };
}

export class AbletonConnection {
  private socket: net.Socket | null = null;
  private decoder = new FrameDecoder();
  private nextId = 1;
  private pending = new Map<number, Pending>();

  constructor(
    private host: string = DEFAULT_HOST,
    private port: number = DEFAULT_PORT,
  ) {}

  async request(
    command: string,
    params: Record<string, unknown> = {},
    timeoutMs: number = DEFAULT_TIMEOUT_MS,
  ): Promise<unknown> {
    try {
      return await this.requestOnce(command, params, timeoutMs);
    } catch (error) {
      if (error instanceof BridgeError) {
        throw error;
      }
      // One reconnect attempt covers Live restarts and script reloads.
      this.close();
      return await this.requestOnce(command, params, timeoutMs);
    }
  }

  close(): void {
    this.socket?.destroy();
    this.socket = null;
    this.failAll(new TransportError("connection closed"));
  }

  private failAll(error: Error): void {
    for (const pending of this.pending.values()) {
      clearTimeout(pending.timer);
      pending.reject(error);
    }
    this.pending.clear();
  }

  private async requestOnce(
    command: string,
    params: Record<string, unknown>,
    timeoutMs: number,
  ): Promise<unknown> {
    const socket = await this.connect();
    const id = this.nextId++;
    return await new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        this.close();
        reject(new TransportError(`timed out waiting for response to '${command}'`));
      }, timeoutMs);
      this.pending.set(id, { resolve, reject, timer });
      socket.write(encode({ id, command, params }));
    });
  }

  private connect(): Promise<net.Socket> {
    if (this.socket && !this.socket.destroyed) {
      return Promise.resolve(this.socket);
    }
    return new Promise((resolve, reject) => {
      const socket = net.connect({ host: this.host, port: this.port });
      socket.setNoDelay(true);
      socket.setTimeout(CONNECT_TIMEOUT_MS, () => socket.destroy(new Error("timeout")));

      socket.once("connect", () => {
        socket.setTimeout(0);
        this.socket = socket;
        this.decoder = new FrameDecoder();
        resolve(socket);
      });
      socket.on("error", (error) => {
        if (this.socket === socket) {
          this.socket = null;
          this.failAll(new TransportError(String(error)));
        } else {
          reject(
            new TransportError(
              NOT_RUNNING_HINT.replace("{host}", this.host).replace(
                "{port}", String(this.port),
              ),
            ),
          );
        }
      });
      socket.on("close", () => {
        if (this.socket === socket) {
          this.socket = null;
          this.failAll(new TransportError("bridge closed the connection"));
        }
      });
      socket.on("data", (data) => this.onData(data));
    });
  }

  private onData(data: Buffer): void {
    let messages: unknown[];
    try {
      messages = this.decoder.feed(data);
    } catch (error) {
      if (error instanceof FrameError) {
        this.close();
        return;
      }
      throw error;
    }
    for (const raw of messages) {
      const message = raw as Response;
      if (typeof message.id !== "number") continue;
      const pending = this.pending.get(message.id);
      if (!pending) continue;
      this.pending.delete(message.id);
      clearTimeout(pending.timer);
      if (message.status === "ok") {
        pending.resolve(message.result);
      } else {
        pending.reject(
          new BridgeError(
            message.error?.type ?? "unknown",
            message.error?.message ?? "unknown bridge error",
          ),
        );
      }
    }
  }
}

let connection: AbletonConnection | null = null;

export function getConnection(): AbletonConnection {
  connection ??= new AbletonConnection();
  return connection;
}
