// Wire framing for the Live bridge: 4-byte big-endian length prefix + UTF-8
// JSON. Must stay wire-compatible with remote_script/AbletonMCP/core/protocol.py.

const HEADER_SIZE = 4;
export const MAX_FRAME_BYTES = 16 * 1024 * 1024;

export class FrameError extends Error {}

export function encode(message: unknown): Buffer {
  const body = Buffer.from(JSON.stringify(message), "utf-8");
  if (body.length > MAX_FRAME_BYTES) {
    throw new FrameError(`frame of ${body.length} bytes exceeds limit`);
  }
  const frame = Buffer.alloc(HEADER_SIZE + body.length);
  frame.writeUInt32BE(body.length, 0);
  body.copy(frame, HEADER_SIZE);
  return frame;
}

export class FrameDecoder {
  private buffer: Buffer = Buffer.alloc(0);

  feed(data: Buffer): unknown[] {
    this.buffer = Buffer.concat([this.buffer, data]);
    const messages: unknown[] = [];
    while (this.buffer.length >= HEADER_SIZE) {
      const length = this.buffer.readUInt32BE(0);
      if (length > MAX_FRAME_BYTES) {
        throw new FrameError(`frame of ${length} bytes exceeds limit`);
      }
      if (this.buffer.length < HEADER_SIZE + length) {
        break;
      }
      const body = this.buffer.subarray(HEADER_SIZE, HEADER_SIZE + length);
      this.buffer = this.buffer.subarray(HEADER_SIZE + length);
      try {
        messages.push(JSON.parse(body.toString("utf-8")));
      } catch (error) {
        throw new FrameError(`invalid frame payload: ${error}`);
      }
    }
    return messages;
  }
}
