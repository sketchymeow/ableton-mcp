"""Generic LOM access: get/set/call/describe on any path, plus ping.

This layer is what makes the bridge cover the full Live API without a
hand-written command per property.
"""

from ..core import lom
from ..core.registry import CommandError

PROTOCOL_VERSION = 1


def register(registry, roots):
    def get_property(params):
        obj = lom.resolve(roots, _require(params, "path"))
        name = _require(params, "property")
        try:
            value = getattr(obj, name)
        except AttributeError:
            raise CommandError(
                "%r has no property %r" % (type(obj).__name__, name),
                error_type="lom_path_error",
            )
        return {"value": lom.safe_value(value)}

    def set_property(params):
        obj = lom.resolve(roots, _require(params, "path"))
        name = _require(params, "property")
        if "value" not in params:
            raise CommandError("missing param: value")
        value = params["value"]
        try:
            setattr(obj, name, value)
        except TypeError:
            # Live is strict about float properties; JSON turns 1.0 into 1.
            if isinstance(value, int) and not isinstance(value, bool):
                setattr(obj, name, float(value))
            else:
                raise
        return {"value": lom.safe_value(getattr(obj, name))}

    def call_method(params):
        obj = lom.resolve(roots, _require(params, "path"))
        name = _require(params, "method")
        args = params.get("args") or []
        if not isinstance(args, list):
            raise CommandError("args must be a list")
        try:
            method = getattr(obj, name)
        except AttributeError:
            raise CommandError(
                "%r has no method %r" % (type(obj).__name__, name),
                error_type="lom_path_error",
            )
        if not callable(method):
            raise CommandError("%r is a property, not a method" % name)
        return {"result": lom.safe_value(method(*args))}

    def describe(params):
        return lom.describe(lom.resolve(roots, _require(params, "path")))

    def ping(params):
        return {
            "pong": True,
            "protocol_version": PROTOCOL_VERSION,
            "live_version": _live_version(),
        }

    registry.register_all(
        {
            "get_property": get_property,
            "set_property": set_property,
            "call_method": call_method,
            "describe": describe,
            "ping": ping,
        }
    )


def _require(params, key):
    try:
        return params[key]
    except KeyError:
        raise CommandError("missing param: %s" % key)


def _live_version():
    try:
        import Live

        app = Live.Application.get_application()
        return "%d.%d.%d" % (
            app.get_major_version(),
            app.get_minor_version(),
            app.get_bugfix_version(),
        )
    except Exception:
        return None
