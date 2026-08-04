"""Non-blocking TCP server pumped from Live's main thread.

No background threads: BridgeServer.tick() is called every ~100ms by the
control surface (via schedule_message), so every handler runs on Live's main
thread by construction. Clients speak the length-prefixed JSON protocol.
"""

import socket
import traceback

from .protocol import FrameDecoder, FrameError, encode
from .registry import CommandError

RECV_BYTES_PER_TICK = 256 * 1024


class _Client(object):
    def __init__(self, sock):
        self.sock = sock
        self.decoder = FrameDecoder()
        self.outbox = bytearray()


class BridgeServer(object):
    def __init__(self, registry, host="127.0.0.1", port=9877, logger=None):
        self._registry = registry
        self._logger = logger
        self._clients = []
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((host, port))
        self._sock.listen(4)
        self._sock.setblocking(False)
        self.port = self._sock.getsockname()[1]

    def tick(self):
        self._accept()
        for client in list(self._clients):
            self._service(client)

    def _accept(self):
        while True:
            try:
                sock, _ = self._sock.accept()
            except (BlockingIOError, OSError):
                return
            sock.setblocking(False)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self._clients.append(_Client(sock))
            self._log("client connected")

    def _service(self, client):
        try:
            while True:
                try:
                    data = client.sock.recv(RECV_BYTES_PER_TICK)
                except (BlockingIOError, InterruptedError):
                    break
                if not data:
                    self._drop(client, "client disconnected")
                    return
                for message in client.decoder.feed(data):
                    client.outbox.extend(encode(self._handle(message)))
                if len(data) < RECV_BYTES_PER_TICK:
                    break
            self._flush(client)
        except FrameError as exc:
            self._drop(client, "framing error: %s" % exc)
        except OSError as exc:
            self._drop(client, "socket error: %s" % exc)

    def _handle(self, message):
        message_id = message.get("id") if isinstance(message, dict) else None
        if not isinstance(message, dict) or "command" not in message:
            return _error(message_id, "bad_request", "expected {id, command, params}")
        try:
            result = self._registry.dispatch(message["command"], message.get("params"))
            return {"id": message_id, "status": "ok", "result": result}
        except CommandError as exc:
            return _error(message_id, exc.error_type, str(exc))
        except Exception as exc:
            self._log("handler crash: %s" % traceback.format_exc())
            return _error(message_id, "internal_error", "%s: %s" % (type(exc).__name__, exc))

    def _flush(self, client):
        if not client.outbox:
            return
        try:
            sent = client.sock.send(bytes(client.outbox))
            del client.outbox[:sent]
        except (BlockingIOError, InterruptedError):
            pass

    def _drop(self, client, reason):
        self._log(reason)
        try:
            client.sock.close()
        except OSError:
            pass
        if client in self._clients:
            self._clients.remove(client)

    def close(self):
        for client in list(self._clients):
            self._drop(client, "server shutting down")
        try:
            self._sock.close()
        except OSError:
            pass

    def _log(self, text):
        if self._logger is not None:
            self._logger(text)


def _error(message_id, error_type, message):
    return {
        "id": message_id,
        "status": "error",
        "error": {"type": error_type, "message": message},
    }
