"""Clip CRUD, firing, properties, and arrangement placement."""

from typing import Literal

from ..connection import get_connection

Location = Literal["session", "arrangement"]


def _clip_ref(track_index, scene_index, clip_index, location):
    ref = {"track_index": track_index, "location": location}
    if location == "session":
        ref["scene_index"] = scene_index
    else:
        ref["clip_index"] = clip_index
    return ref


def register(mcp):
    @mcp.tool()
    def clip_slot(
        action: Literal["create", "delete", "fire", "stop"],
        track_index: int,
        scene_index: int,
        length: float = 4.0,
    ) -> dict:
        """Work with a session clip slot: create an empty MIDI clip (length in
        beats), delete the clip, or fire/stop it. Firing respects launch
        quantization."""
        params = {"track_index": track_index, "scene_index": scene_index}
        if action == "create":
            params["length"] = length
        return get_connection().request(f"{action}_clip", params)

    @mcp.tool()
    def get_clip(
        track_index: int,
        scene_index: int = -1,
        location: Location = "session",
        clip_index: int = -1,
    ) -> dict:
        """Get a clip's properties: loop points, markers, launch settings,
        playback state, and (for audio clips) gain/pitch/warp settings. Use
        scene_index for session clips, clip_index for arrangement clips."""
        return get_connection().request(
            "get_clip", _clip_ref(track_index, scene_index, clip_index, location)
        )

    @mcp.tool()
    def set_clip(
        track_index: int,
        scene_index: int = -1,
        location: Location = "session",
        clip_index: int = -1,
        name: str | None = None,
        color: str | None = None,
        looping: bool | None = None,
        loop_start: float | None = None,
        loop_end: float | None = None,
        start_marker: float | None = None,
        end_marker: float | None = None,
        launch_mode: int | None = None,
        launch_quantization: int | None = None,
        legato: bool | None = None,
        muted: bool | None = None,
        gain: float | None = None,
        pitch_coarse: int | None = None,
        pitch_fine: float | None = None,
        warping: bool | None = None,
        warp_mode: int | None = None,
    ) -> dict:
        """Set clip properties in one call. Only the arguments you pass are
        changed. Times are in beats; color is "#RRGGBB"; gain/pitch/warp apply
        to audio clips only."""
        skip = {"track_index", "scene_index", "location", "clip_index"}
        params = {k: v for k, v in locals().items()
                  if v is not None and k not in skip and k != "skip"}
        params.update(_clip_ref(track_index, scene_index, clip_index, location))
        return get_connection().request("set_clip", params)

    @mcp.tool()
    def arrangement_clips(track_index: int) -> dict:
        """List a track's arrangement clips with their timeline positions."""
        return get_connection().request(
            "get_arrangement_clips", {"track_index": track_index}
        )

    @mcp.tool()
    def clip_to_arrangement(track_index: int, scene_index: int, time: float) -> dict:
        """Copy a session clip onto the arrangement timeline at the given
        time (in beats). This is how you build a song structure from session
        clips."""
        return get_connection().request(
            "clip_to_arrangement",
            {"track_index": track_index, "scene_index": scene_index, "time": time},
        )
