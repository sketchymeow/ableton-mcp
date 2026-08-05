import { describe, expect, it } from "vitest";
import { encode, FrameDecoder, FrameError } from "../src/protocol.js";

describe("framing", () => {
  it("round-trips a message", () => {
    const decoder = new FrameDecoder();
    const message = { id: 1, command: "ping", params: { x: "héllo" } };
    expect(decoder.feed(encode(message))).toEqual([message]);
  });

  it("handles byte-at-a-time feeds", () => {
    const decoder = new FrameDecoder();
    const data = encode({ id: 2 });
    for (let i = 0; i < data.length - 1; i++) {
      expect(decoder.feed(data.subarray(i, i + 1))).toEqual([]);
    }
    expect(decoder.feed(data.subarray(data.length - 1))).toEqual([{ id: 2 }]);
  });

  it("decodes multiple frames from one feed", () => {
    const decoder = new FrameDecoder();
    const data = Buffer.concat([encode({ id: 1 }), encode({ id: 2 }), encode({ id: 3 })]);
    expect(decoder.feed(data).map((m) => (m as { id: number }).id)).toEqual([1, 2, 3]);
  });

  it("rejects oversized frames", () => {
    const decoder = new FrameDecoder();
    const header = Buffer.alloc(4);
    header.writeUInt32BE(2 ** 31 - 1, 0);
    expect(() => decoder.feed(header)).toThrow(FrameError);
  });

  it("rejects invalid payloads", () => {
    const decoder = new FrameDecoder();
    const header = Buffer.alloc(4);
    header.writeUInt32BE(3, 0);
    expect(() => decoder.feed(Buffer.concat([header, Buffer.from("{{{")]))).toThrow(
      FrameError,
    );
  });

  it("matches the python wire format byte for byte", () => {
    // Same message the python test suite round-trips; prefix must be
    // 4-byte big-endian length.
    const frame = encode({ id: 7 });
    expect(frame.readUInt32BE(0)).toBe(frame.length - 4);
    expect(frame.subarray(4).toString("utf-8")).toBe('{"id":7}');
  });
});
