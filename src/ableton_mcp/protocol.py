"""Wire framing for the Live bridge: 4-byte big-endian length prefix + UTF-8 JSON.

This file must stay identical to remote_script/AbletonMCP/core/protocol.py
(the remote script has to be self-contained). A unit test enforces the sync.
"""

import json
import struct

HEADER = struct.Struct(">I")
MAX_FRAME_BYTES = 16 * 1024 * 1024


class FrameError(Exception):
    """Unrecoverable framing error. The connection should be closed."""


def encode(message):
    body = json.dumps(message, ensure_ascii=False).encode("utf-8")
    if len(body) > MAX_FRAME_BYTES:
        raise FrameError("frame of %d bytes exceeds limit" % len(body))
    return HEADER.pack(len(body)) + body


class FrameDecoder:
    """Accumulates bytes, yields decoded messages as complete frames arrive."""

    def __init__(self):
        self._buffer = bytearray()

    def feed(self, data):
        self._buffer.extend(data)
        messages = []
        while len(self._buffer) >= HEADER.size:
            (length,) = HEADER.unpack(bytes(self._buffer[: HEADER.size]))
            if length > MAX_FRAME_BYTES:
                raise FrameError("frame of %d bytes exceeds limit" % length)
            if len(self._buffer) < HEADER.size + length:
                break
            body = bytes(self._buffer[HEADER.size : HEADER.size + length])
            del self._buffer[: HEADER.size + length]
            try:
                messages.append(json.loads(body.decode("utf-8")))
            except (ValueError, UnicodeDecodeError) as exc:
                raise FrameError("invalid frame payload: %s" % exc)
        return messages
