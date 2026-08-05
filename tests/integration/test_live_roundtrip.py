"""End-to-end tests against a real Ableton Live instance.

Run with Live open and the AbletonMCP control surface enabled:

    ABLETON_MCP_LIVE_TESTS=1 uv run pytest tests/integration -v

These create and delete a scratch track; they don't touch existing tracks.
"""

import socket

import pytest

from AbletonMCP.core.protocol import FrameDecoder, encode

pytestmark = pytest.mark.live


class BridgeClient:
    """Minimal test client speaking the bridge protocol directly."""

    def __init__(self, host="127.0.0.1", port=9877):
        self.sock = socket.create_connection((host, port), timeout=15.0)
        self.decoder = FrameDecoder()
        self.next_id = 1

    def request(self, command, params=None):
        request_id = self.next_id
        self.next_id += 1
        self.sock.sendall(encode({"id": request_id, "command": command,
                                  "params": params or {}}))
        while True:
            for message in self.decoder.feed(self.sock.recv(65536)):
                if message.get("id") != request_id:
                    continue
                if message.get("status") == "ok":
                    return message.get("result")
                raise AssertionError(message.get("error"))

    def close(self):
        self.sock.close()


@pytest.fixture(scope="module")
def conn():
    client = BridgeClient()
    yield client
    client.close()


@pytest.fixture()
def scratch_track(conn):
    track = conn.request("create_track", {"type": "midi"})
    yield track["index"]
    conn.request("delete_track", {"track_index": track["index"]})


def test_ping(conn):
    result = conn.request("ping")
    assert result["pong"] is True
    assert result["live_version"]


def test_track_roundtrip(conn, scratch_track):
    conn.request("set_track", {"track_index": scratch_track, "name": "MCP Scratch"})
    detail = conn.request("get_track", {"track_index": scratch_track})
    assert detail["name"] == "MCP Scratch"


def test_notes_roundtrip(conn, scratch_track):
    clip = {"track_index": scratch_track, "scene_index": 0}
    conn.request("create_clip", dict(clip, length=4.0))
    conn.request(
        "add_notes",
        dict(clip, notes=[
            {"pitch": 60, "start_time": 0.0, "duration": 1.0},
            {"pitch": 64, "start_time": 1.0, "duration": 1.0},
            {"pitch": 67, "start_time": 2.0, "duration": 1.0},
        ]),
    )
    notes = conn.request("get_notes", clip)["notes"]
    assert sorted(n["pitch"] for n in notes) == [60, 64, 67]
    first_id = notes[0]["note_id"]
    conn.request("update_notes",
                 dict(clip, notes=[{"note_id": first_id, "velocity": 40}]))
    updated = conn.request("get_notes", clip)["notes"]
    assert any(n["velocity"] == 40 for n in updated)


def test_automation_roundtrip(conn, scratch_track):
    clip = {"track_index": scratch_track, "scene_index": 0}
    conn.request("create_clip", dict(clip, length=4.0))
    target = dict(clip, mixer_parameter="volume")
    conn.request(
        "write_automation",
        dict(target, points=[{"time": 0.0, "value": 0.2},
                             {"time": 4.0, "value": 0.8}]),
    )
    read = conn.request("read_automation", dict(target, times=[0.0]))
    assert read["has_envelope"] is True


def test_event_feed(conn):
    conn.request("subscribe", {"path": "song", "property": "tempo"})
    try:
        result = conn.request("poll_events", {})
        assert result["events"], "baseline event expected"
    finally:
        conn.request("unsubscribe", {})
