import pytest

from AbletonMCP.core.protocol import FrameDecoder, FrameError, HEADER, encode


def test_roundtrip():
    decoder = FrameDecoder()
    message = {"id": 1, "command": "ping", "params": {"x": "héllo"}}
    assert decoder.feed(encode(message)) == [message]


def test_partial_feeds():
    decoder = FrameDecoder()
    data = encode({"id": 2})
    for byte_index in range(len(data) - 1):
        assert decoder.feed(data[byte_index : byte_index + 1]) == []
    assert decoder.feed(data[-1:]) == [{"id": 2}]


def test_multiple_frames_in_one_feed():
    decoder = FrameDecoder()
    data = encode({"id": 1}) + encode({"id": 2}) + encode({"id": 3})
    assert [m["id"] for m in decoder.feed(data)] == [1, 2, 3]


def test_oversized_frame_rejected():
    decoder = FrameDecoder()
    with pytest.raises(FrameError):
        decoder.feed(HEADER.pack(2**31))


def test_invalid_payload_rejected():
    decoder = FrameDecoder()
    with pytest.raises(FrameError):
        decoder.feed(HEADER.pack(3) + b"{{{")
