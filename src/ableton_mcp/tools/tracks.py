"""Track listing, CRUD, properties, and routing."""

from typing import Literal

from ..connection import get_connection

TrackType = Literal["track", "return", "master"]


def register(mcp):
    @mcp.tool()
    def list_tracks() -> dict:
        """List all tracks (regular, return, and master) with type, name,
        color, mute/solo/arm state, devices, and clip counts."""
        return get_connection().request("get_tracks")

    @mcp.tool()
    def get_track(track_index: int, track_type: TrackType = "track") -> dict:
        """Get one track in detail: summary plus monitoring, fold state, clip
        slots, and current/available input and output routing."""
        return get_connection().request(
            "get_track", {"track_index": track_index, "track_type": track_type}
        )

    @mcp.tool()
    def create_track(
        type: Literal["midi", "audio", "return"] = "midi", index: int = -1
    ) -> dict:
        """Create a track. index -1 appends at the end (return tracks always
        append). Returns the new track's summary including its index."""
        return get_connection().request("create_track", {"type": type, "index": index})

    @mcp.tool()
    def delete_track(track_index: int, track_type: TrackType = "track") -> dict:
        """Delete a track or return track. The master track cannot be
        deleted."""
        return get_connection().request(
            "delete_track", {"track_index": track_index, "track_type": track_type}
        )

    @mcp.tool()
    def duplicate_track(track_index: int) -> dict:
        """Duplicate a regular track, including its devices and clips. The
        copy lands right after the original."""
        return get_connection().request("duplicate_track", {"track_index": track_index})

    @mcp.tool()
    def set_track(
        track_index: int,
        track_type: TrackType = "track",
        name: str | None = None,
        color: str | None = None,
        arm: bool | None = None,
        mute: bool | None = None,
        solo: bool | None = None,
        monitoring: Literal["in", "auto", "off"] | None = None,
        fold_state: int | None = None,
    ) -> dict:
        """Set track properties in one call. Only the arguments you pass are
        changed. color is "#RRGGBB"."""
        params = {
            k: v
            for k, v in locals().items()
            if v is not None and k not in ("track_index", "track_type")
        }
        params["track_index"] = track_index
        params["track_type"] = track_type
        return get_connection().request("set_track", params)

    @mcp.tool()
    def track_routing(
        track_index: int,
        track_type: TrackType = "track",
        input_type: str | None = None,
        input_channel: str | None = None,
        output_type: str | None = None,
        output_channel: str | None = None,
    ) -> dict:
        """Get or set track routing. With no routing arguments this returns
        the current and available options; pass display names from the
        available lists to change routing."""
        conn = get_connection()
        changes = {
            k: v
            for k, v in {
                "input_type": input_type,
                "input_channel": input_channel,
                "output_type": output_type,
                "output_channel": output_channel,
            }.items()
            if v is not None
        }
        base = {"track_index": track_index, "track_type": track_type}
        if not changes:
            return conn.request("get_track_routing", base)
        return conn.request("set_track_routing", dict(base, **changes))
