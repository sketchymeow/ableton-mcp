"""Resolve Live Object Model paths like song.tracks[2].devices[0].parameters[3].

Roots are injected as a dict of {name: thunk} so tests can substitute fakes.
"""

import re

from .registry import CommandError

_SEGMENT = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)((?:\[\d+\])*)$")
_INDEX = re.compile(r"\[(\d+)\]")


class LomPathError(CommandError):
    def __init__(self, message):
        super(LomPathError, self).__init__(message, error_type="lom_path_error")


def resolve(roots, path):
    if not path or not isinstance(path, str):
        raise LomPathError("path must be a non-empty string")

    segments = path.split(".")
    match = _SEGMENT.match(segments[0])
    if not match:
        raise LomPathError("bad path segment: %r" % segments[0])
    root_name = match.group(1)
    if root_name not in roots:
        raise LomPathError(
            "unknown root %r; valid roots: %s" % (root_name, ", ".join(sorted(roots)))
        )
    obj = roots[root_name]()
    obj = _apply_indexes(obj, match.group(2), segments[0])

    for segment in segments[1:]:
        match = _SEGMENT.match(segment)
        if not match:
            raise LomPathError("bad path segment: %r" % segment)
        name = match.group(1)
        try:
            obj = getattr(obj, name)
        except AttributeError:
            raise LomPathError(
                "%r has no attribute %r (path %r)" % (type(obj).__name__, name, path)
            )
        obj = _apply_indexes(obj, match.group(2), segment)

    return obj


def _apply_indexes(obj, index_text, segment):
    for index_match in _INDEX.finditer(index_text):
        index = int(index_match.group(1))
        try:
            obj = obj[index]
        except (IndexError, TypeError):
            raise LomPathError("index %d out of range in segment %r" % (index, segment))
    return obj


def safe_value(value, depth=0):
    """Convert a LOM value into something JSON-serializable."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    if depth >= 4:
        return {"__type__": type(value).__name__}
    if isinstance(value, (list, tuple)) or type(value).__name__.endswith("Vector"):
        return [safe_value(item, depth + 1) for item in value]
    summary = {"__type__": type(value).__name__}
    name = getattr(value, "name", None)
    if not isinstance(name, str):
        name = getattr(value, "display_name", None)
    if isinstance(name, str):
        summary["name"] = name
    return summary


def describe(obj):
    """Introspect a LOM object: properties, methods, and listenable properties."""
    properties = {}
    methods = []
    listenable = []
    for name in dir(obj):
        if name.startswith("_"):
            continue
        if name.startswith("add_") and name.endswith("_listener"):
            listenable.append(name[len("add_") : -len("_listener")])
            continue
        if name.endswith("_listener") or name.endswith("_has_listener"):
            continue
        try:
            attr = getattr(obj, name)
        except Exception as exc:
            properties[name] = {"__error__": str(exc)}
            continue
        if callable(attr):
            methods.append(name)
        else:
            properties[name] = safe_value(attr)
    return {
        "type": type(obj).__name__,
        "properties": properties,
        "methods": sorted(methods),
        "listenable": sorted(listenable),
    }
