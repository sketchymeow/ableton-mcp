"""Live browser: navigate, search, load."""

from typing import Literal

from ..connection import get_connection

Root = Literal[
    "instruments", "sounds", "drums", "audio_effects", "midi_effects",
    "plugins", "samples", "packs", "user_library", "current_project",
]
TrackType = Literal["track", "return", "master"]


def register(mcp):
    @mcp.tool()
    def browse(root: Root = "instruments",
               path: list[str | int] | None = None) -> dict:
        """List one level of Live's browser. path drills down from the root
        by item name or index (e.g. ["Operator"] lists Operator's presets).
        Loadable items have a uri for load_browser_item."""
        return get_connection().request(
            "browse", {"root": root, "path": path or []}, timeout=30.0
        )

    @mcp.tool()
    def search_browser(
        query: str,
        roots: list[Root] | None = None,
        max_results: int = 25,
    ) -> dict:
        """Search the browser by name for loadable devices, presets, and
        sounds. Defaults to instruments/sounds/drums/effects/plugins; pass
        roots to search elsewhere (e.g. samples). The sweep is budgeted, so
        truncated=true means narrow the query or browse directly."""
        params = {"query": query, "max_results": max_results}
        if roots is not None:
            params["roots"] = roots
        return get_connection().request("search_browser", params, timeout=45.0)

    @mcp.tool()
    def load_browser_item(
        uri: str,
        track_index: int | None = None,
        track_type: TrackType = "track",
    ) -> dict:
        """Load a browser item by uri (from browse/search_browser) —
        instruments and effects go onto the given track (or the currently
        selected one if track_index is omitted)."""
        params = {"uri": uri, "track_type": track_type}
        if track_index is not None:
            params["track_index"] = track_index
        return get_connection().request("load_browser_item", params, timeout=60.0)
