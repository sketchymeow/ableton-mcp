"""Generic LOM access: get/set/call/describe on any path, plus ping.

This layer is what makes the bridge cover the full Live API without a
hand-written command per property.
"""

from ..core import lom
from ..core.registry import CommandError
from . import common

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
        if "value_path" in params:
            # Object-valued property: resolve another LOM object and assign it
            # (e.g. view.selected_track, a drum rack's selected_drum_pad).
            setattr(obj, name, lom.resolve(roots, params["value_path"]))
            return {"value": lom.safe_value(getattr(obj, name))}
        if "value" not in params:
            raise CommandError("missing param: value")
        value = params["value"]
        options = common.safe_get(obj, "available_%ss" % name)
        if options:
            # Routing-style property: Live wants an object out of the
            # available_* vector, not a scalar. Accept index or display name.
            setattr(obj, name, _pick_option(options, value, name))
        else:
            common.set_with_float_retry(obj, name, value)
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


def _pick_option(options, value, name):
    if isinstance(value, bool):
        raise CommandError(
            "%s takes an index or display name from available_%ss" % (name, name)
        )
    if isinstance(value, (int, float)):
        index = int(value)
        try:
            return options[index]
        except IndexError:
            raise CommandError(
                "index %d out of range for available_%ss (%d options)"
                % (index, name, len(options))
            )
    wanted = str(value).strip().lower()
    for option in options:
        display = common.safe_get(option, "display_name")
        if display is not None and str(display).lower() == wanted:
            return option
    if wanted.lstrip("-").isdigit():
        return _pick_option(options, int(wanted), name)
    names = [str(common.safe_get(o, "display_name")) for o in options]
    raise CommandError(
        "no %s option matching %r; options: %s" % (name, value, ", ".join(names))
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
