"""Mixer control: volume, pan, sends, crossfader."""

from typing import Literal

from ..connection import get_connection

TrackType = Literal["track", "return", "master"]


def register(mcp):
    @mcp.tool()
    def get_mixer(track_index: int = 0, track_type: TrackType = "track") -> dict:
        """Get a track's mixer state: volume, pan, sends (with the return
        track each one feeds), and crossfade assignment. Values come with
        display strings (e.g. "0.0 dB")."""
        return get_connection().request(
            "get_mixer", {"track_index": track_index, "track_type": track_type}
        )

    @mcp.tool()
    def set_mixer(
        track_index: int = 0,
        track_type: TrackType = "track",
        volume: float | None = None,
        panning: float | None = None,
        crossfade_assign: Literal["A", "none", "B"] | None = None,
        cue_volume: float | None = None,
        crossfader: float | None = None,
    ) -> dict:
        """Set mixer values in one call. volume is 0..1 (0.85 = 0 dB),
        panning is -1..1. cue_volume and crossfader exist on the master track
        only. Returns the updated mixer state with display strings."""
        params = {k: v for k, v in locals().items()
                  if v is not None and k not in ("track_index", "track_type")}
        params["track_index"] = track_index
        params["track_type"] = track_type
        return get_connection().request("set_mixer", params)

    @mcp.tool()
    def set_send(
        track_index: int,
        send_index: int,
        value: float,
        track_type: TrackType = "track",
    ) -> dict:
        """Set a send level (0..1). send_index matches the return track order
        from get_mixer/list_tracks."""
        return get_connection().request(
            "set_send",
            {"track_index": track_index, "track_type": track_type,
             "send_index": send_index, "value": value},
        )
