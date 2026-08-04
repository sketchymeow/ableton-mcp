"""Change feed: LOM property listeners buffered for polling.

MCP is request/response, so Claude can't receive pushes. Instead,
listeners append change events to a bounded ring buffer with monotonic
sequence numbers, and the client polls with its last-seen cursor. This is
how Claude notices tempo changes, track edits, playback state, etc.
between calls.
"""

import time
from collections import deque

from ..core import lom
from ..core.registry import CommandError
from . import common

MAX_EVENTS = 500


def register(registry, roots):
    state = {"seq": 0}
    events = deque(maxlen=MAX_EVENTS)
    listeners = {}

    def _emit(path, prop, target):
        state["seq"] += 1
        try:
            value = lom.safe_value(getattr(target, prop))
        except Exception:
            value = None
        events.append(
            {
                "seq": state["seq"],
                "path": path,
                "property": prop,
                "value": value,
                "time": time.time(),
            }
        )

    def _remove(key):
        target, prop, callback = listeners.pop(key)
        remover = common.safe_get(target, "remove_%s_listener" % prop)
        if remover is not None:
            try:
                remover(callback)
            except Exception:
                pass  # target may be gone (e.g. deleted track); that's fine

    def subscribe(params):
        path = common.require(params, "path")
        prop = common.require(params, "property")
        target = lom.resolve(roots, path)
        adder = common.safe_get(target, "add_%s_listener" % prop)
        if adder is None or not callable(adder):
            raise CommandError(
                "%r is not listenable on this object; live_describe lists "
                "listenable properties" % prop
            )
        key = (path, prop)
        if key in listeners:
            _remove(key)

        def callback():
            _emit(path, prop, target)

        adder(callback)
        listeners[key] = (target, prop, callback)
        _emit(path, prop, target)  # baseline value as the first event
        return {"subscribed": {"path": path, "property": prop},
                "subscriptions": len(listeners)}

    def unsubscribe(params):
        path = params.get("path")
        prop = params.get("property")
        if path is None and prop is None:
            removed = len(listeners)
            for key in list(listeners):
                _remove(key)
            return {"removed": removed}
        key = (common.require(params, "path"), common.require(params, "property"))
        if key not in listeners:
            raise CommandError("no subscription for %s %s" % key)
        _remove(key)
        return {"removed": 1}

    def poll_events(params):
        since = int(params.get("since", 0))
        return {
            "events": [e for e in events if e["seq"] > since],
            "last_seq": state["seq"],
            "subscriptions": [
                {"path": path, "property": prop}
                for path, prop in sorted(listeners)
            ],
        }

    registry.register_all(
        {
            "subscribe": subscribe,
            "unsubscribe": unsubscribe,
            "poll_events": poll_events,
        }
    )
