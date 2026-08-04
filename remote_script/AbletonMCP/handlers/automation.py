"""Clip automation envelopes: write, read, clear.

Targets any automatable DeviceParameter — device parameters (by device
index + parameter name/index) or mixer parameters (volume, panning,
sends, crossfader). Works for session and arrangement clips.
"""

from ..core.registry import CommandError
from . import common
from .device import _find_parameter

MIXER_PARAMS = ("volume", "panning", "cue_volume", "crossfader")


def register(registry, roots):
    def song():
        return roots["song"]()

    def _target_parameter(params):
        s = song()
        track = common.get_track(
            s, common.require(params, "track_index"), params.get("track_type", "track")
        )
        if "device_index" in params:
            devices = common.safe_get(track, "devices", ())
            try:
                device = devices[params["device_index"]]
            except (IndexError, TypeError):
                raise CommandError(
                    "device index %s out of range (%d devices)"
                    % (params["device_index"], len(devices))
                )
            param, _ = _find_parameter(
                common.safe_get(device, "parameters", ()),
                common.require(params, "parameter"),
            )
            return param
        mixer_parameter = params.get("mixer_parameter")
        if mixer_parameter is not None:
            mixer = common.safe_get(track, "mixer_device")
            if mixer is None:
                raise CommandError("this track has no mixer device")
            if mixer_parameter == "send":
                sends = common.safe_get(mixer, "sends", ())
                index = common.require(params, "send_index")
                try:
                    return sends[index]
                except (IndexError, TypeError):
                    raise CommandError(
                        "send index %s out of range (%d sends)" % (index, len(sends))
                    )
            if mixer_parameter not in MIXER_PARAMS:
                raise CommandError(
                    "mixer_parameter must be one of: %s, send"
                    % ", ".join(MIXER_PARAMS)
                )
            param = common.safe_get(mixer, mixer_parameter)
            if param is None:
                raise CommandError("this mixer has no %s" % mixer_parameter)
            return param
        raise CommandError(
            "specify a target: device_index + parameter, or mixer_parameter"
        )

    def _envelope(clip, param):
        envelope = clip.automation_envelope(param)
        if envelope is None:
            create = common.safe_get(clip, "create_automation_envelope")
            if create is None:
                raise CommandError("could not create an automation envelope")
            envelope = create(param)
        if envelope is None:
            raise CommandError("no automation envelope for that parameter")
        return envelope

    def write_automation(params):
        clip = common.get_clip(song(), params)
        param = _target_parameter(params)
        points = params.get("points")
        if not isinstance(points, list) or not points:
            raise CommandError("points must be a non-empty list of {time, value}")
        if params.get("clear_first"):
            clip.clear_envelope(param)
        envelope = _envelope(clip, param)
        for i, point in enumerate(points):
            if not isinstance(point, dict) or "time" not in point or "value" not in point:
                raise CommandError("point %d must have time and value" % i)
            envelope.insert_step(
                float(point["time"]),
                float(point.get("length", 0.0)),
                float(point["value"]),
            )
        return {"written": len(points), "parameter": common.safe_get(param, "name")}

    def read_automation(params):
        clip = common.get_clip(song(), params)
        param = _target_parameter(params)
        envelope = clip.automation_envelope(param)
        if envelope is None:
            return {"has_envelope": False, "points": []}
        times = params.get("times")
        if times is None:
            length = float(common.safe_get(clip, "length", 4.0))
            steps = int(params.get("samples", 17))
            if steps < 2:
                raise CommandError("samples must be at least 2")
            times = [length * i / (steps - 1) for i in range(steps)]
        return {
            "has_envelope": True,
            "parameter": common.safe_get(param, "name"),
            "points": [
                {"time": float(t), "value": envelope.value_at_time(float(t))}
                for t in times
            ],
        }

    def clear_automation(params):
        clip = common.get_clip(song(), params)
        if ("device_index" in params) or ("mixer_parameter" in params):
            clip.clear_envelope(_target_parameter(params))
            return {"cleared": "parameter"}
        clip.clear_all_envelopes()
        return {"cleared": "all"}

    registry.register_all(
        {
            "write_automation": write_automation,
            "read_automation": read_automation,
            "clear_automation": clear_automation,
        }
    )
