"""Live browser: navigate, search, and load devices/presets/samples.

The browser tree is huge and lazy, so nothing walks it whole. browse() is
one level at a time, search() is a breadth-first sweep with a node budget,
and every loadable item seen is cached by URI so load_browser_item can
find it again without another walk.
"""

from ..core.registry import CommandError
from . import common

ROOT_NAMES = (
    "instruments",
    "sounds",
    "drums",
    "audio_effects",
    "midi_effects",
    "plugins",
    "samples",
    "packs",
    "user_library",
    "current_project",
)

DEFAULT_SEARCH_ROOTS = (
    "instruments",
    "sounds",
    "drums",
    "audio_effects",
    "midi_effects",
    "plugins",
)

SEARCH_NODE_BUDGET = 4000


def _item_summary(item, index=None):
    summary = {
        "name": common.safe_get(item, "name"),
        "is_folder": common.safe_get(item, "is_folder"),
        "is_loadable": common.safe_get(item, "is_loadable"),
    }
    uri = common.safe_get(item, "uri")
    if uri:
        summary["uri"] = uri
    if index is not None:
        summary["index"] = index
    return summary


def register(registry, roots):
    item_cache = {}

    def browser():
        app = roots["app"]()
        b = common.safe_get(app, "browser")
        if b is None:
            raise CommandError("browser is not available")
        return b

    def _root(name):
        if name not in ROOT_NAMES:
            raise CommandError(
                "unknown root %r; roots: %s" % (name, ", ".join(ROOT_NAMES))
            )
        item = common.safe_get(browser(), name)
        if item is None:
            raise CommandError("browser root %r is not available" % name)
        return item

    def _cache(item):
        uri = common.safe_get(item, "uri")
        if uri and common.safe_get(item, "is_loadable"):
            item_cache[uri] = item

    def browse(params):
        item = _root(params.get("root", "instruments"))
        path = params.get("path") or []
        crumbs = [common.safe_get(item, "name")]
        for step in path:
            children = common.safe_get(item, "children", ())
            if isinstance(step, int):
                try:
                    item = children[step]
                except (IndexError, TypeError):
                    raise CommandError(
                        "index %s out of range under %s (%d children)"
                        % (step, " > ".join(crumbs), len(children))
                    )
            else:
                matches = [
                    c for c in children
                    if str(common.safe_get(c, "name", "")).lower() == str(step).lower()
                ]
                if not matches:
                    names = [str(common.safe_get(c, "name")) for c in children]
                    raise CommandError(
                        "no item named %r under %s; children: %s"
                        % (step, " > ".join(crumbs), ", ".join(names[:40]))
                    )
                item = matches[0]
            crumbs.append(common.safe_get(item, "name"))
        children = common.safe_get(item, "children", ())
        result = []
        for i, child in enumerate(children):
            _cache(child)
            result.append(_item_summary(child, index=i))
        return {"path": crumbs, "items": result}

    def search(params):
        query = str(common.require(params, "query")).lower()
        root_names = params.get("roots") or list(DEFAULT_SEARCH_ROOTS)
        max_results = int(params.get("max_results", 25))
        matches = []
        visited = 0
        truncated = False
        for root_name in root_names:
            queue = [(_root(root_name), [root_name])]
            while queue:
                if visited >= SEARCH_NODE_BUDGET or len(matches) >= max_results:
                    truncated = visited >= SEARCH_NODE_BUDGET
                    break
                item, path = queue.pop(0)
                visited += 1
                _cache(item)
                name = str(common.safe_get(item, "name", ""))
                if query in name.lower() and common.safe_get(item, "is_loadable"):
                    matches.append(
                        dict(_item_summary(item), path=" > ".join(path))
                    )
                if common.safe_get(item, "is_folder") or not common.safe_get(
                    item, "is_loadable"
                ):
                    for child in common.safe_get(item, "children", ()):
                        queue.append((child, path + [common.safe_get(child, "name")]))
            if len(matches) >= max_results:
                break
        return {"matches": matches, "truncated": truncated}

    def _find_by_uri(uri):
        if uri in item_cache:
            return item_cache[uri]
        visited = 0
        for root_name in ROOT_NAMES:
            try:
                queue = [_root(root_name)]
            except CommandError:
                continue
            while queue and visited < SEARCH_NODE_BUDGET:
                item = queue.pop(0)
                visited += 1
                _cache(item)
                if common.safe_get(item, "uri") == uri:
                    return item
                queue.extend(common.safe_get(item, "children", ()))
        raise CommandError(
            "no browser item with uri %r; use search_browser or browse first" % uri
        )

    def load_browser_item(params):
        uri = common.require(params, "uri")
        item = _find_by_uri(uri)
        if not common.safe_get(item, "is_loadable"):
            raise CommandError("%r is not loadable" % common.safe_get(item, "name"))
        song = roots["song"]()
        if "track_index" in params:
            track = common.get_track(
                song, params["track_index"], params.get("track_type", "track")
            )
            song.view.selected_track = track
        browser().load_item(item)
        return {"loaded": common.safe_get(item, "name"), "uri": uri}

    registry.register_all(
        {
            "browse": browse,
            "search_browser": search,
            "load_browser_item": load_browser_item,
        }
    )
