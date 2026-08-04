"""Clip automation envelopes."""

from typing import Any, Literal

from ..connection import get_connection

Location = Literal["session", "arrangement"]
MixerParam = Literal["volume", "panning", "cue_volume", "crossfader", "send"]


def _params(track_index, scene_index, clip_index, location, device_index,
            parameter, mixer_parameter, send_index):
    params = {"track_index": track_index, "location": location}
    if location == "session":
        params["scene_index"] = scene_index
    else:
        params["clip_index"] = clip_index
    if device_index is not None:
        params["device_index"] = device_index
        params["parameter"] = parameter
    if mixer_parameter is not None:
        params["mixer_parameter"] = mixer_parameter
        if send_index is not None:
            params["send_index"] = send_index
    return params


def register(mcp):
    @mcp.tool()
    def write_automation(
        track_index: int,
        points: list[dict[str, Any]],
        scene_index: int = -1,
        location: Location = "session",
        clip_index: int = -1,
        device_index: int | None = None,
        parameter: int | str | None = None,
        mixer_parameter: MixerParam | None = None,
        send_index: int | None = None,
        clear_first: bool = False,
    ) -> dict:
        """Write an automation envelope into a clip — filter sweeps, volume
        ramps, etc. Target a device parameter (device_index + parameter) or a
        mixer parameter (mixer_parameter, with send_index for sends). Each
        point is {time, value} in beats/parameter units; optional length
        holds the value flat for that many beats. Set clear_first to replace
        the existing envelope."""
        params = _params(track_index, scene_index, clip_index, location,
                         device_index, parameter, mixer_parameter, send_index)
        params["points"] = points
        params["clear_first"] = clear_first
        return get_connection().request("write_automation", params)

    @mcp.tool()
    def read_automation(
        track_index: int,
        scene_index: int = -1,
        location: Location = "session",
        clip_index: int = -1,
        device_index: int | None = None,
        parameter: int | str | None = None,
        mixer_parameter: MixerParam | None = None,
        send_index: int | None = None,
        times: list[float] | None = None,
        samples: int = 17,
    ) -> dict:
        """Read an automation envelope's values. Pass times (in beats) for
        exact points, or let it sample the clip evenly (samples points).
        has_envelope is false if the parameter has no automation."""
        params = _params(track_index, scene_index, clip_index, location,
                         device_index, parameter, mixer_parameter, send_index)
        if times is not None:
            params["times"] = times
        else:
            params["samples"] = samples
        return get_connection().request("read_automation", params)

    @mcp.tool()
    def clear_automation(
        track_index: int,
        scene_index: int = -1,
        location: Location = "session",
        clip_index: int = -1,
        device_index: int | None = None,
        parameter: int | str | None = None,
        mixer_parameter: MixerParam | None = None,
        send_index: int | None = None,
    ) -> dict:
        """Clear automation from a clip: pass a target to clear one
        parameter's envelope, or no target to clear every envelope in the
        clip."""
        params = _params(track_index, scene_index, clip_index, location,
                         device_index, parameter, mixer_parameter, send_index)
        return get_connection().request("clear_automation", params)
