"""Mixer reads and writes: volume, pan, sends, crossfader."""

from ..core.registry import CommandError
from . import common

CROSSFADE_NAMES = {0: "A", 1: "none", 2: "B"}
CROSSFADE_VALUES = dict((v, k) for k, v in CROSSFADE_NAMES.items())


def param_info(param, name=None):
    if param is None:
        return None
    info = {
        "name": name or common.safe_get(param, "name"),
        "value": common.safe_get(param, "value"),
        "min": common.safe_get(param, "min"),
        "max": common.safe_get(param, "max"),
    }
    display = display_value(param)
    if display is not None:
        info["display"] = display
    return info


def display_value(param):
    try:
        return param.str_for_value(param.value)
    except Exception:
        return None


def register(registry, roots):
    def song():
        return roots["song"]()

    def _mixer(params):
        track = common.get_track(
            song(),
            params.get("track_index", 0),
            params.get("track_type", "track"),
        )
        mixer = common.safe_get(track, "mixer_device")
        if mixer is None:
            raise CommandError("this track has no mixer device")
        return mixer

    def get_mixer(params):
        s = song()
        mixer = _mixer(params)
        result = {
            "volume": param_info(mixer.volume),
            "panning": param_info(mixer.panning),
            "sends": [
                dict(
                    param_info(
                        send, name=common.safe_get(s.return_tracks[i], "name")
                        if i < len(s.return_tracks) else None
                    ),
                    index=i,
                )
                for i, send in enumerate(common.safe_get(mixer, "sends", ()))
            ],
        }
        assign = common.safe_get(mixer, "crossfade_assign")
        if assign is not None:
            result["crossfade_assign"] = CROSSFADE_NAMES.get(assign, assign)
        for extra in ("cue_volume", "crossfader"):
            param = common.safe_get(mixer, extra)
            if param is not None:
                result[extra] = param_info(param)
        return result

    def set_mixer(params):
        mixer = _mixer(params)
        settable = ("volume", "panning", "cue_volume", "crossfader")
        touched = False
        for name in settable:
            if name not in params:
                continue
            param = common.safe_get(mixer, name)
            if param is None:
                raise CommandError("this mixer has no %s" % name)
            common.set_with_float_retry(param, "value", params[name])
            touched = True
        if "crossfade_assign" in params:
            value = params["crossfade_assign"]
            if value not in CROSSFADE_VALUES:
                raise CommandError("crossfade_assign must be 'A', 'none', or 'B'")
            mixer.crossfade_assign = CROSSFADE_VALUES[value]
            touched = True
        if not touched:
            raise CommandError(
                "nothing to set; settable: %s, crossfade_assign" % ", ".join(settable)
            )
        return get_mixer(params)

    def set_send(params):
        mixer = _mixer(params)
        sends = common.safe_get(mixer, "sends", ())
        index = common.require(params, "send_index")
        try:
            send = sends[index]
        except (IndexError, TypeError):
            raise CommandError(
                "send index %s out of range (%d sends)" % (index, len(sends))
            )
        common.set_with_float_retry(send, "value", common.require(params, "value"))
        return dict(param_info(send), index=index)

    registry.register_all(
        {"get_mixer": get_mixer, "set_mixer": set_mixer, "set_send": set_send}
    )
