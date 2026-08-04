"""TCP client for the AbletonMCP remote script bridge."""

import itertools
import socket
import time

from .protocol import FrameDecoder, FrameError, encode

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9877
DEFAULT_TIMEOUT = 12.0

NOT_RUNNING_HINT = (
    "Could not reach Ableton Live on {host}:{port}. Make sure Live is running "
    "and the AbletonMCP control surface is enabled in "
    "Settings > Link/Tempo/MIDI."
)


class BridgeError(Exception):
    """The bridge returned a structured error for a command."""

    def __init__(self, error_type: str, message: str):
        super().__init__(message)
        self.error_type = error_type


class AbletonConnection:
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self._sock: socket.socket | None = None
        self._decoder = FrameDecoder()
        self._ids = itertools.count(1)

    def _connect(self) -> socket.socket:
        if self._sock is None:
            try:
                self._sock = socket.create_connection(
                    (self.host, self.port), timeout=5.0
                )
                self._sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            except OSError as exc:
                raise ConnectionError(
                    NOT_RUNNING_HINT.format(host=self.host, port=self.port)
                ) from exc
            self._decoder = FrameDecoder()
        return self._sock

    def close(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def request(self, command: str, params: dict | None = None,
                timeout: float = DEFAULT_TIMEOUT):
        """Send one command and wait for its response. Raises BridgeError on
        structured errors, ConnectionError on transport problems."""
        try:
            return self._request_once(command, params, timeout)
        except (ConnectionError, OSError, FrameError):
            # One reconnect attempt covers Live restarts and script reloads.
            self.close()
            return self._request_once(command, params, timeout)

    def _request_once(self, command, params, timeout):
        sock = self._connect()
        request_id = next(self._ids)
        sock.settimeout(timeout)
        sock.sendall(encode({"id": request_id, "command": command,
                             "params": params or {}}))
        deadline = time.monotonic() + timeout
        while True:
            if time.monotonic() > deadline:
                self.close()
                raise ConnectionError(
                    f"timed out waiting for response to {command!r}"
                )
            data = sock.recv(65536)
            if not data:
                self.close()
                raise ConnectionError("bridge closed the connection")
            for message in self._decoder.feed(data):
                if message.get("id") != request_id:
                    continue
                if message.get("status") == "ok":
                    return message.get("result")
                error = message.get("error") or {}
                raise BridgeError(
                    error.get("type", "unknown"),
                    error.get("message", "unknown bridge error"),
                )


_connection: AbletonConnection | None = None


def get_connection() -> AbletonConnection:
    global _connection
    if _connection is None:
        _connection = AbletonConnection()
    return _connection
