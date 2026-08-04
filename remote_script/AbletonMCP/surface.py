"""The ControlSurface Live loads. Only importable inside Live."""

import logging
import os

from ableton.v2.control_surface import ControlSurface

from .core.registry import Registry
from .core.server import BridgeServer
from .handlers import register_all

PORT = 9877

logger = logging.getLogger("abletonmcp")


class AbletonMCPSurface(ControlSurface):
    def __init__(self, c_instance):
        super(AbletonMCPSurface, self).__init__(c_instance)
        self._bridge = None
        self._start_logging()
        try:
            registry = Registry()
            register_all(registry, self._roots())
            self._bridge = BridgeServer(registry, port=PORT, logger=logger.info)
            self.schedule_message(0, self._tick)
            self.show_message("AbletonMCP: listening on 127.0.0.1:%d" % PORT)
            logger.info("started on port %d" % PORT)
        except OSError as exc:
            self.show_message("AbletonMCP: couldn't bind port %d (%s)" % (PORT, exc))
            logger.error("couldn't bind port %d (%s)" % (PORT, exc))

    def _roots(self):
        def get_song():
            song = self.song
            return song() if callable(song) else song

        def get_app():
            import Live

            return Live.Application.get_application()

        return {"song": get_song, "app": get_app}

    def _tick(self):
        try:
            self._bridge.tick()
        except Exception:
            logger.exception("tick failed")
        self.schedule_message(1, self._tick)

    def _start_logging(self):
        log_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "logs")
        if not os.path.exists(log_dir):
            os.mkdir(log_dir, 0o755)
        handler = logging.FileHandler(os.path.join(log_dir, "abletonmcp.log"))
        handler.setFormatter(
            logging.Formatter("(%(asctime)s) [%(levelname)s] %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def disconnect(self):
        if self._bridge is not None:
            self._bridge.close()
        logger.info("disconnected")
        super(AbletonMCPSurface, self).disconnect()
