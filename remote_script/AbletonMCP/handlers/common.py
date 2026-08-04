"""Shared helpers for handler modules."""

from ..core.registry import CommandError

MONITORING_NAMES = {0: "in", 1: "auto", 2: "off"}
MONITORING_VALUES = dict((v, k) for k, v in MONITORING_NAMES.items())


def require(params, key):
    try:
        return params[key]
    except KeyError:
        raise CommandError("missing param: %s" % key)


def safe_get(obj, name, default=None):
    try:
        return getattr(obj, name)
    except Exception:
        return default


def get_track(song, index, track_type="track"):
    if track_type == "master":
        return song.master_track
    if track_type == "track":
        vector = song.tracks
    elif track_type == "return":
        vector = song.return_tracks
    else:
        raise CommandError(
            "track_type must be 'track', 'return', or 'master', not %r" % track_type
        )
    try:
        return vector[index]
    except (IndexError, TypeError):
        raise CommandError(
            "%s index %s out of range (%d available)"
            % (track_type, index, len(vector))
        )


def get_scene(song, index):
    try:
        return song.scenes[index]
    except (IndexError, TypeError):
        raise CommandError(
            "scene index %s out of range (%d scenes)" % (index, len(song.scenes))
        )


def parse_color(value):
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.lstrip("#")
        if len(text) == 6:
            try:
                return int(text, 16)
            except ValueError:
                pass
    raise CommandError("color must be an int or '#RRGGBB', not %r" % value)


def format_color(value):
    if not isinstance(value, int):
        return None
    return "#%06X" % (value & 0xFFFFFF)


def track_summary(track, index, track_type="track"):
    if track_type == "master":
        kind = "master"
    elif track_type == "return":
        kind = "return"
    elif safe_get(track, "is_foldable"):
        kind = "group"
    elif safe_get(track, "has_midi_input"):
        kind = "midi"
    else:
        kind = "audio"

    summary = {
        "index": index,
        "type": kind,
        "name": safe_get(track, "name"),
        "color": format_color(safe_get(track, "color")),
        "mute": safe_get(track, "mute"),
        "solo": safe_get(track, "solo"),
        "devices": [safe_get(d, "name") for d in safe_get(track, "devices", ())],
    }
    if safe_get(track, "can_be_armed"):
        summary["arm"] = safe_get(track, "arm")
    slots = safe_get(track, "clip_slots")
    if slots is not None:
        summary["num_clips"] = sum(1 for slot in slots if safe_get(slot, "has_clip"))
        summary["playing_slot_index"] = safe_get(track, "playing_slot_index")
    if safe_get(track, "is_grouped"):
        summary["is_grouped"] = True
    return summary


def scene_summary(scene, index):
    summary = {
        "index": index,
        "name": safe_get(scene, "name"),
        "color": format_color(safe_get(scene, "color")),
        "is_empty": safe_get(scene, "is_empty"),
        "is_triggered": safe_get(scene, "is_triggered"),
    }
    tempo = safe_get(scene, "tempo")
    if isinstance(tempo, (int, float)) and tempo > 0:
        summary["tempo"] = tempo
    return summary


def get_clip_slot(song, track_index, scene_index):
    track = get_track(song, track_index)
    slots = safe_get(track, "clip_slots")
    if slots is None:
        raise CommandError("this track has no clip slots")
    try:
        return slots[scene_index]
    except (IndexError, TypeError):
        raise CommandError(
            "scene index %s out of range (%d slots)" % (scene_index, len(slots))
        )


def get_clip(song, params):
    """Resolve a clip reference: session (track_index + scene_index) or
    arrangement (track_index + clip_index with location='arrangement')."""
    location = params.get("location", "session")
    track_index = require(params, "track_index")
    if location == "session":
        slot = get_clip_slot(song, track_index, require(params, "scene_index"))
        if not safe_get(slot, "has_clip"):
            raise CommandError(
                "no clip at track %s scene %s" % (track_index, params["scene_index"])
            )
        return slot.clip
    if location == "arrangement":
        track = get_track(song, track_index)
        clips = safe_get(track, "arrangement_clips")
        if clips is None:
            raise CommandError("this track has no arrangement clips")
        clip_index = require(params, "clip_index")
        try:
            return clips[clip_index]
        except (IndexError, TypeError):
            raise CommandError(
                "arrangement clip index %s out of range (%d clips)"
                % (clip_index, len(clips))
            )
    raise CommandError("location must be 'session' or 'arrangement'")


def set_with_float_retry(obj, name, value):
    try:
        setattr(obj, name, value)
    except TypeError:
        if isinstance(value, int) and not isinstance(value, bool):
            setattr(obj, name, float(value))
        else:
            raise
