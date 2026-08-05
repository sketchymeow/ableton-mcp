import type { McpServer } from "@modelcontextprotocol/server";
import { getConnection } from "../connection.js";

export type Registrar = (server: McpServer) => void;

export function json(result: unknown) {
  return { content: [{ type: "text" as const, text: JSON.stringify(result) }] };
}

export async function bridge(
  command: string,
  params: Record<string, unknown> = {},
  timeoutMs?: number,
) {
  return json(await getConnection().request(command, params, timeoutMs));
}

/** Drop undefined values so optional tool args never reach the bridge. */
export function compact(params: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== undefined),
  );
}
