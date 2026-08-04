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
    def live_set(path: str, property: str, value: bool | int | float | str) -> dict:
        """Set a property on any Live Object Model path. Returns the value after
        the write so you can confirm it took (Live clamps out-of-range values)."""
        return get_connection().request(
            "set_property", {"path": path, "property": property, "value": value}
        )

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
