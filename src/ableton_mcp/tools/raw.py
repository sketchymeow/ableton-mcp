"""Generic Live Object Model access. Full API coverage, minimal ergonomics."""

from typing import Any

from ..connection import get_connection


def register(mcp):
    @mcp.tool()
    def ping() -> dict:
        """Check the connection to Ableton Live. Returns the Live version if
        reachable. Use this first if other tools are failing."""
        return get_connection().request("ping")

    @mcp.tool()
    def live_get(path: str, property: str) -> dict:
        """Read a property from any Live Object Model path.

        Examples: path="song" property="tempo", path="song.tracks[0]"
        property="name", path="song.tracks[0].devices[0].parameters[3]"
        property="value". Use live_describe to discover paths and properties."""
        return get_connection().request(
            "get_property", {"path": path, "property": property}
        )

    @mcp.tool()
    def live_set(
        path: str,
        property: str,
        value: bool | int | float | str | None = None,
        value_path: str | None = None,
    ) -> dict:
        """Set a property on any Live Object Model path. Returns the value
        after the write so you can confirm it took (Live clamps out-of-range
        values).

        Routing-style properties (ones with an available_* sibling, like a
        compressor's sidechain input_routing_type) accept an index or display
        name and resolve to the right object. For other object-valued
        properties (view.selected_track, a drum rack view's
        selected_drum_pad), pass value_path with the LOM path of the object
        to assign instead of value."""
        params = {"path": path, "property": property}
        if value_path is not None:
            params["value_path"] = value_path
        else:
            params["value"] = value
        return get_connection().request("set_property", params)

    @mcp.tool()
    def live_call(path: str, method: str, args: list[Any] | None = None) -> dict:
        """Call a method on any Live Object Model path.

        Examples: path="song" method="create_midi_track" args=[-1],
        path="song" method="start_playing"."""
        return get_connection().request(
            "call_method", {"path": path, "method": method, "args": args or []}
        )

    @mcp.tool()
    def live_describe(path: str) -> dict:
        """Introspect a Live Object Model path: its properties with current
        values, callable methods, and listenable properties. Start at
        path="song" or path="app" and drill down."""
        return get_connection().request("describe", {"path": path})
