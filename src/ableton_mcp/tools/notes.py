"""MIDI note editing with stable note IDs."""

from typing import Any, Literal

from ..connection import get_connection

Location = Literal["session", "arrangement"]


def _ref(track_index, scene_index, clip_index, location):
    ref = {"track_index": track_index, "location": location}
    if location == "session":
        ref["scene_index"] = scene_index
    else:
        ref["clip_index"] = clip_index
    return ref


def register(mcp):
    @mcp.tool()
    def get_notes(
        track_index: int,
        scene_index: int = -1,
        location: Location = "session",
        clip_index: int = -1,
        from_pitch: int | None = None,
        pitch_span: int | None = None,
        from_time: float | None = None,
        time_span: float | None = None,
    ) -> dict:
        """Read the MIDI notes in a clip. Each note has a stable note_id you
        can use with update_notes/remove_notes. Omit the range arguments to
        get every note; pass them to read a pitch/time window (times in
        beats)."""
        params = _ref(track_index, scene_index, clip_index, location)
        for key, value in {
            "from_pitch": from_pitch, "pitch_span": pitch_span,
            "from_time": from_time, "time_span": time_span,
        }.items():
            if value is not None:
                params[key] = value
        return get_connection().request("get_notes", params)

    @mcp.tool()
    def add_notes(
        track_index: int,
        notes: list[dict[str, Any]],
        scene_index: int = -1,
        location: Location = "session",
        clip_index: int = -1,
    ) -> dict:
        """Add MIDI notes to a clip without touching existing ones. Each note
        needs pitch (0-127), start_time and duration (beats); optional
        velocity (0-127, default 100), mute, probability (0-1),
        velocity_deviation, release_velocity. Returns all notes in the clip
        with their IDs."""
        params = _ref(track_index, scene_index, clip_index, location)
        params["notes"] = notes
        return get_connection().request("add_notes", params)

    @mcp.tool()
    def update_notes(
        track_index: int,
        notes: list[dict[str, Any]],
        scene_index: int = -1,
        location: Location = "session",
        clip_index: int = -1,
    ) -> dict:
        """Modify existing notes by ID. Each entry needs the note_id from
        get_notes plus the fields to change (pitch, start_time, duration,
        velocity, mute, probability, velocity_deviation, release_velocity)."""
        params = _ref(track_index, scene_index, clip_index, location)
        params["notes"] = notes
        return get_connection().request("update_notes", params)

    @mcp.tool()
    def remove_notes(
        track_index: int,
        scene_index: int = -1,
        location: Location = "session",
        clip_index: int = -1,
        note_ids: list[int] | None = None,
        from_pitch: int | None = None,
        pitch_span: int | None = None,
        from_time: float | None = None,
        time_span: float | None = None,
    ) -> dict:
        """Remove notes from a clip: pass note_ids for specific notes, or a
        pitch/time range. With neither, every note in the clip is removed."""
        params = _ref(track_index, scene_index, clip_index, location)
        if note_ids is not None:
            params["note_ids"] = note_ids
        for key, value in {
            "from_pitch": from_pitch, "pitch_span": pitch_span,
            "from_time": from_time, "time_span": time_span,
        }.items():
            if value is not None:
                params[key] = value
        return get_connection().request("remove_notes", params)
