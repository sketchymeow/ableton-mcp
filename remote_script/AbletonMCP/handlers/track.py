"""Track CRUD, batched property writes, and routing."""

from ..core.registry import CommandError
from . import common

SETTABLE = frozenset(
    ["name", "color", "arm", "mute", "solo", "fold_state", "monitoring"]
)

ROUTING_FIELDS = {
    "input_type": ("input_routing_type", "available_input_routing_types"),
    "input_channel": ("input_routing_channel", "available_input_routing_channels"),
    "output_type": ("output_routing_type", "available_output_routing_types"),
    "output_channel": ("output_routing_channel", "available_output_routing_channels"),
}


def register(registry, roots):
    def song():
        return roots["song"]()

    def _track(params):
        track_type = params.get("track_type", "track")
        return (
            common.get_track(song(), common.require(params, "track_index"), track_type),
            track_type,
        )

    def create_track(params):
        s = song()
        track_type = params.get("type", "midi")
        index = params.get("index", -1)
        if track_type == "midi":
            s.create_midi_track(index)
            new_index = index if index >= 0 else len(s.tracks) - 1
            track = s.tracks[new_index]
        elif track_type == "audio":
            s.create_audio_track(index)
            new_index = index if index >= 0 else len(s.tracks) - 1
            track = s.tracks[new_index]
        elif track_type == "return":
            s.create_return_track()
            new_index = len(s.return_tracks) - 1
            track = s.return_tracks[new_index]
        else:
            raise CommandError("type must be 'midi', 'audio', or 'return'")
        kind = "return" if track_type == "return" else "track"
        return common.track_summary(track, new_index, kind)

    def delete_track(params):
        s = song()
        index = common.require(params, "track_index")
        track_type = params.get("track_type", "track")
        common.get_track(s, index, track_type)  # range check
        if track_type == "track":
            s.delete_track(index)
        elif track_type == "return":
            s.delete_return_track(index)
        else:
            raise CommandError("cannot delete the master track")
        return {"deleted": index}

    def duplicate_track(params):
        s = song()
        index = common.require(params, "track_index")
        common.get_track(s, index, "track")
        s.duplicate_track(index)
        return common.track_summary(s.tracks[index + 1], index + 1)

    def get_track(params):
        track, track_type = _track(params)
        index = params["track_index"]
        kind = track_type if track_type != "track" else "track"
        detail = common.track_summary(track, index, kind)
        detail["monitoring"] = common.MONITORING_NAMES.get(
            common.safe_get(track, "current_monitoring_state")
        )
        detail["fold_state"] = common.safe_get(track, "fold_state")
        slots = common.safe_get(track, "clip_slots")
        if slots is not None:
            detail["clip_slots"] = [
                {
                    "index": i,
                    "has_clip": common.safe_get(slot, "has_clip"),
                    "clip_name": common.safe_get(
                        common.safe_get(slot, "clip"), "name"
                    ),
                }
                for i, slot in enumerate(slots)
            ]
        detail["routing"] = _get_routing(track)
        return detail

    def set_track(params):
        track, track_type = _track(params)
        props = dict(params)
        props.pop("track_index", None)
        props.pop("track_type", None)
        unknown = sorted(set(props) - SETTABLE)
        if unknown:
            raise CommandError(
                "cannot set %s; settable: %s"
                % (", ".join(unknown), ", ".join(sorted(SETTABLE)))
            )
        for name, value in props.items():
            if name == "color":
                value = common.parse_color(value)
            elif name == "monitoring":
                if value not in common.MONITORING_VALUES:
                    raise CommandError("monitoring must be 'in', 'auto', or 'off'")
                name, value = "current_monitoring_state", common.MONITORING_VALUES[value]
            elif name == "arm" and not common.safe_get(track, "can_be_armed"):
                raise CommandError("this track cannot be armed")
            common.set_with_float_retry(track, name, value)
        index = params["track_index"]
        kind = track_type if track_type != "track" else "track"
        return common.track_summary(track, index, kind)

    def get_track_routing(params):
        track, _ = _track(params)
        return _get_routing(track)

    def set_track_routing(params):
        track, _ = _track(params)
        for field in ROUTING_FIELDS:
            if field not in params:
                continue
            wanted = params[field]
            current_attr, available_attr = ROUTING_FIELDS[field]
            available = common.safe_get(track, available_attr, ())
            match = None
            for option in available:
                if common.safe_get(option, "display_name") == wanted:
                    match = option
                    break
            if match is None:
                names = [common.safe_get(o, "display_name") for o in available]
                raise CommandError(
                    "no %s named %r; available: %s" % (field, wanted, ", ".join(names))
                )
            setattr(track, current_attr, match)
        return _get_routing(track)

    registry.register_all(
        {
            "create_track": create_track,
            "delete_track": delete_track,
            "duplicate_track": duplicate_track,
            "get_track": get_track,
            "set_track": set_track,
            "get_track_routing": get_track_routing,
            "set_track_routing": set_track_routing,
        }
    )


def _get_routing(track):
    routing = {}
    for field, (current_attr, available_attr) in ROUTING_FIELDS.items():
        current = common.safe_get(track, current_attr)
        routing[field] = common.safe_get(current, "display_name")
        routing["available_%ss" % field] = [
            common.safe_get(option, "display_name")
            for option in common.safe_get(track, available_attr, ())
        ]
    return routing
