"""Change feed: subscribe to Live properties and poll for changes."""

from ..connection import get_connection


def register(mcp):
    @mcp.tool()
    def live_subscribe(path: str, property: str) -> dict:
        """Subscribe to changes of a Live Object Model property (e.g.
        path="song" property="tempo", or path="song.tracks[0]"
        property="playing_slot_index"). Changes accumulate in a buffer you
        read with live_poll_events. live_describe lists which properties are
        listenable."""
        return get_connection().request(
            "subscribe", {"path": path, "property": property}
        )

    @mcp.tool()
    def live_unsubscribe(path: str | None = None, property: str | None = None) -> dict:
        """Remove one subscription (path + property) or all of them (no
        arguments)."""
        params = {}
        if path is not None:
            params["path"] = path
        if property is not None:
            params["property"] = property
        return get_connection().request("unsubscribe", params)

    @mcp.tool()
    def live_poll_events(since: int = 0) -> dict:
        """Read buffered change events past the given cursor. Use last_seq
        from the previous poll as since. Call this before acting on a session
        you haven't touched recently — the user may have changed things."""
        return get_connection().request("poll_events", {"since": since})
