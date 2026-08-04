"""Clip CRUD, firing, properties, and arrangement placement."""

from ..core.registry import CommandError
from . import common

SETTABLE = frozenset(
    [
        "name",
        "color",
        "looping",
        "loop_start",
        "loop_end",
        "start_marker",
        "end_marker",
        "launch_mode",
        "launch_quantization",
        "legato",
        "muted",
        "velocity_amount",
        "ram_mode",
        "gain",
        "pitch_coarse",
        "pitch_fine",
        "warping",
        "warp_mode",
        "signature_numerator",
        "signature_denominator",
    ]
)

INFO_PROPS = [
    "name",
    "length",
    "looping",
    "loop_start",
    "loop_end",
    "start_marker",
    "end_marker",
    "launch_mode",
    "launch_quantization",
    "legato",
    "muted",
    "is_playing",
    "is_recording",
    "is_triggered",
    "is_midi_clip",
    "is_audio_clip",
    "playing_position",
    "signature_numerator",
    "signature_denominator",
    "start_time",
    "end_time",
    "gain",
    "pitch_coarse",
    "pitch_fine",
    "warping",
    "warp_mode",
    "file_path",
]


def clip_info(clip):
    info = {}
    for prop in INFO_PROPS:
        value = common.safe_get(clip, prop, default=None)
        if value is not None:
            info[prop] = value
    color = common.safe_get(clip, "color")
    if color is not None:
        info["color"] = common.format_color(color)
    return info


def register(registry, roots):
    def song():
        return roots["song"]()

    def create_clip(params):
        slot = common.get_clip_slot(
            song(),
            common.require(params, "track_index"),
            common.require(params, "scene_index"),
        )
        if common.safe_get(slot, "has_clip"):
            raise CommandError("slot already has a clip; delete it first")
        slot.create_clip(float(params.get("length", 4.0)))
        return clip_info(slot.clip)

    def delete_clip(params):
        if params.get("location") == "arrangement":
            track = common.get_track(song(), common.require(params, "track_index"))
            clip = common.get_clip(song(), params)
            track.delete_clip(clip)
            return {"deleted": True}
        slot = common.get_clip_slot(
            song(),
            common.require(params, "track_index"),
            common.require(params, "scene_index"),
        )
        if not common.safe_get(slot, "has_clip"):
            raise CommandError("no clip in that slot")
        slot.delete_clip()
        return {"deleted": True}

    def fire_clip(params):
        slot = common.get_clip_slot(
            song(),
            common.require(params, "track_index"),
            common.require(params, "scene_index"),
        )
        slot.fire()
        return {"fired": True}

    def stop_clip(params):
        slot = common.get_clip_slot(
            song(),
            common.require(params, "track_index"),
            common.require(params, "scene_index"),
        )
        slot.stop()
        return {"stopped": True}

    def get_clip(params):
        return clip_info(common.get_clip(song(), params))

    def set_clip(params):
        clip = common.get_clip(song(), params)
        props = dict(params)
        for key in ("track_index", "scene_index", "clip_index", "location"):
            props.pop(key, None)
        unknown = sorted(set(props) - SETTABLE)
        if unknown:
            raise CommandError(
                "cannot set %s; settable: %s"
                % (", ".join(unknown), ", ".join(sorted(SETTABLE)))
            )
        for name, value in props.items():
            if name == "color":
                value = common.parse_color(value)
            common.set_with_float_retry(clip, name, value)
        return clip_info(clip)

    def get_arrangement_clips(params):
        track = common.get_track(song(), common.require(params, "track_index"))
        clips = common.safe_get(track, "arrangement_clips", ())
        return {
            "clips": [
                dict(clip_info(clip), clip_index=i) for i, clip in enumerate(clips)
            ]
        }

    def clip_to_arrangement(params):
        track = common.get_track(song(), common.require(params, "track_index"))
        clip = common.get_clip(song(), dict(params, location="session"))
        time = float(common.require(params, "time"))
        track.duplicate_clip_to_arrangement(clip, time)
        return {"placed_at": time}

    registry.register_all(
        {
            "create_clip": create_clip,
            "delete_clip": delete_clip,
            "fire_clip": fire_clip,
            "stop_clip": stop_clip,
            "get_clip": get_clip,
            "set_clip": set_clip,
            "get_arrangement_clips": get_arrangement_clips,
            "clip_to_arrangement": clip_to_arrangement,
        }
    )
