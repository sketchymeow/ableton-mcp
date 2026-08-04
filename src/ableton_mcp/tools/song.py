"""Transport, song settings, and cue points."""

from typing import Literal

from ..connection import get_connection

TRANSPORT_METHODS = {
    "play": "start_playing",
    "stop": "stop_playing",
    "continue": "continue_playing",
    "stop_all_clips": "stop_all_clips",
    "undo": "undo",
    "redo": "redo",
    "tap_tempo": "tap_tempo",
}


def register(mcp):
    @mcp.tool()
    def song_status() -> dict:
        """Get the song state in one call: tempo, time signature, playback,
        loop region, recording state, quantization, and track/scene counts."""
        return get_connection().request("get_song_status")

    @mcp.tool()
    def transport(
        action: Literal[
            "play", "stop", "continue", "stop_all_clips", "undo", "redo", "tap_tempo"
        ],
        position: float | None = None,
    ) -> dict:
        """Control playback. "play" restarts from the last start point,
        "continue" resumes from the current position. Pass position (in beats)
        to jump there first."""
        conn = get_connection()
        if position is not None:
            conn.request(
                "set_property",
                {"path": "song", "property": "current_song_time", "value": position},
            )
        conn.request("call_method", {"path": "song", "method": TRANSPORT_METHODS[action]})
        return conn.request("get_song_status")

    @mcp.tool()
    def set_song(
        tempo: float | None = None,
        signature_numerator: int | None = None,
        signature_denominator: int | None = None,
        metronome: bool | None = None,
        loop: bool | None = None,
        loop_start: float | None = None,
        loop_length: float | None = None,
        record_mode: bool | None = None,
        session_record: bool | None = None,
        clip_trigger_quantization: int | None = None,
        midi_recording_quantization: int | None = None,
        groove_amount: float | None = None,
    ) -> dict:
        """Set song-level properties in one call. Only the arguments you pass
        are changed. Returns the updated song status."""
        params = {k: v for k, v in locals().items() if v is not None}
        return get_connection().request("set_song", params)

    @mcp.tool()
    def cue_points(
        action: Literal["list", "jump_next", "jump_prev", "jump_to", "toggle_at_playhead"],
        index: int | None = None,
    ) -> dict:
        """Work with arrangement locators. "jump_to" needs the index from
        "list". "toggle_at_playhead" creates or deletes a locator at the
        current position."""
        conn = get_connection()
        if action == "list":
            return conn.request("get_cue_points")
        method = {
            "jump_next": ("song", "jump_to_next_cue"),
            "jump_prev": ("song", "jump_to_prev_cue"),
            "toggle_at_playhead": ("song", "set_or_delete_cue"),
        }
        if action == "jump_to":
            if index is None:
                raise ValueError("jump_to needs an index; call with action='list' first")
            conn.request(
                "call_method", {"path": f"song.cue_points[{index}]", "method": "jump"}
            )
        else:
            path, name = method[action]
            conn.request("call_method", {"path": path, "method": name})
        return conn.request("get_cue_points")
