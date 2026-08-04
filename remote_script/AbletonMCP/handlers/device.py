"""Device listing (including racks/chains/drum pads) and parameter control."""

from ..core.registry import CommandError
from . import common
from .mixer import display_value, param_info

MAX_DEPTH = 4

TRACK_PATHS = {
    "track": "song.tracks[%d]",
    "return": "song.return_tracks[%d]",
    "master": "song.master_track",
}


def _track_path(track_type, track_index):
    template = TRACK_PATHS[track_type]
    return template % track_index if "%d" in template else template


def _device_info(device, index, path, depth=0):
    info = {
        "index": index,
        "path": path,
        "name": common.safe_get(device, "name"),
        "class_name": common.safe_get(device, "class_name"),
        "is_active": common.safe_get(device, "is_active"),
        "num_parameters": len(common.safe_get(device, "parameters", ())),
    }
    if common.safe_get(device, "can_have_chains") and depth < MAX_DEPTH:
        info["chains"] = [
            {
                "index": i,
                "name": common.safe_get(chain, "name"),
                "devices": [
                    _device_info(
                        nested, j, "%s.chains[%d].devices[%d]" % (path, i, j),
                        depth + 1,
                    )
                    for j, nested in enumerate(common.safe_get(chain, "devices", ()))
                ],
            }
            for i, chain in enumerate(common.safe_get(device, "chains", ()))
        ]
    if common.safe_get(device, "can_have_drum_pads") and depth < MAX_DEPTH:
        info["drum_pads"] = [
            {
                "note": common.safe_get(pad, "note"),
                "name": common.safe_get(pad, "name"),
                "num_chains": len(common.safe_get(pad, "chains", ())),
            }
            for pad in common.safe_get(device, "drum_pads", ())
            if common.safe_get(pad, "chains")
        ]
    return info


def _parameter_info(param, index):
    info = dict(param_info(param), index=index)
    if common.safe_get(param, "is_quantized"):
        info["is_quantized"] = True
        info["value_items"] = [str(v) for v in common.safe_get(param, "value_items", ())]
    return info


def register(registry, roots):
    def song():
        return roots["song"]()

    def _track(params):
        track_type = params.get("track_type", "track")
        track_index = params.get("track_index", 0)
        return common.get_track(song(), track_index, track_type), track_type, track_index

    def _device(params):
        track, _, _ = _track(params)
        devices = common.safe_get(track, "devices", ())
        index = common.require(params, "device_index")
        try:
            return devices[index], track
        except (IndexError, TypeError):
            raise CommandError(
                "device index %s out of range (%d devices)" % (index, len(devices))
            )

    def get_devices(params):
        track, track_type, track_index = _track(params)
        prefix = _track_path(track_type, track_index)
        return {
            "devices": [
                _device_info(device, i, "%s.devices[%d]" % (prefix, i))
                for i, device in enumerate(common.safe_get(track, "devices", ()))
            ]
        }

    def get_device_parameters(params):
        device, _ = _device(params)
        return {
            "device": common.safe_get(device, "name"),
            "parameters": [
                _parameter_info(param, i)
                for i, param in enumerate(common.safe_get(device, "parameters", ()))
            ],
        }

    def set_device_parameter(params):
        device, _ = _device(params)
        parameters = common.safe_get(device, "parameters", ())
        selector = common.require(params, "parameter")
        param, index = _find_parameter(parameters, selector)
        value = common.require(params, "value")
        if isinstance(value, str):
            # Option name first; otherwise a number that arrived as a string
            # (MCP clients often stringify numbers on int/float-or-str fields).
            items = [str(v) for v in common.safe_get(param, "value_items", ())]
            matches = [i for i, item in enumerate(items) if item.lower() == value.lower()]
            if matches:
                param.value = float(matches[0])
            else:
                try:
                    number = float(value)
                except ValueError:
                    raise CommandError(
                        "%r is not a value of %r; options: %s"
                        % (value, common.safe_get(param, "name"),
                           ", ".join(items) or "none (pass a number)")
                    )
                common.set_with_float_retry(param, "value", number)
        else:
            common.set_with_float_retry(param, "value", value)
        return _parameter_info(param, index)

    def delete_device(params):
        device, track = _device(params)
        track.delete_device(params["device_index"])
        return {"deleted": common.safe_get(device, "name")}

    registry.register_all(
        {
            "get_devices": get_devices,
            "get_device_parameters": get_device_parameters,
            "set_device_parameter": set_device_parameter,
            "delete_device": delete_device,
        }
    )


def _find_parameter(parameters, selector):
    if isinstance(selector, int):
        try:
            return parameters[selector], selector
        except (IndexError, TypeError):
            raise CommandError(
                "parameter index %s out of range (%d parameters)"
                % (selector, len(parameters))
            )
    wanted = str(selector).lower()
    matches = [
        (param, i)
        for i, param in enumerate(parameters)
        if str(common.safe_get(param, "name", "")).lower() == wanted
    ]
    if not matches:
        # An index that arrived as a string ("3") falls back to index lookup.
        stripped = wanted.strip()
        if stripped.lstrip("-").isdigit():
            return _find_parameter(parameters, int(stripped))
        names = [str(common.safe_get(p, "name")) for p in parameters]
        raise CommandError(
            "no parameter named %r; available: %s" % (selector, ", ".join(names))
        )
    return matches[0]
