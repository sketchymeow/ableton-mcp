"""Drives BridgeServer over real sockets, pumping tick() by hand."""

import socket
import time

import pytest

from AbletonMCP.core.protocol import FrameDecoder, encode
from AbletonMCP.core.registry import Registry
from AbletonMCP.core.server import BridgeServer
from AbletonMCP.handlers import raw

from .fake_live import default_song


@pytest.fixture
def server():
    registry = Registry()
    raw.register(registry, {"song": lambda: default_song()})
    server = BridgeServer(registry, port=0)
    yield server
    server.close()


def connect(server):
    sock = socket.create_connection(("127.0.0.1", server.port), timeout=2.0)
    sock.settimeout(2.0)
    return sock


def exchange(server, sock, message, ticks=10):
    sock.sendall(encode(message))
    decoder = FrameDecoder()
    for _ in range(ticks):
        server.tick()
        try:
            data = sock.recv(65536)
        except socket.timeout:
            continue
        messages = decoder.feed(data)
        if messages:
            return messages[0]
        time.sleep(0.01)
    raise AssertionError("no response after %d ticks" % ticks)


def test_request_response(server):
    sock = connect(server)
    response = exchange(
        server,
        sock,
        {"id": 7, "command": "get_property",
         "params": {"path": "song", "property": "tempo"}},
    )
    assert response == {"id": 7, "status": "ok", "result": {"value": 120.0}}


def test_error_response(server):
    sock = connect(server)
    response = exchange(server, sock, {"id": 8, "command": "bogus", "params": {}})
    assert response["status"] == "error"
    assert response["error"]["type"] == "unknown_command"


def test_bad_request_shape(server):
    sock = connect(server)
    response = exchange(server, sock, {"id": 9})
    assert response["status"] == "error"
    assert response["error"]["type"] == "bad_request"


def test_two_clients(server):
    first, second = connect(server), connect(server)
    ping = {"command": "ping", "params": {}}
    assert exchange(server, first, dict(ping, id=1))["id"] == 1
    assert exchange(server, second, dict(ping, id=2))["id"] == 2


def test_malformed_frame_drops_client(server):
    sock = connect(server)
    sock.sendall(b"\x00\x00\x00\x03{{{")
    for _ in range(5):
        server.tick()
    # Server closed us; a clean recv of b"" proves it.
    assert sock.recv(1) == b""


def test_binds_localhost_only(server):
    assert server._sock.getsockname()[0] == "127.0.0.1"
