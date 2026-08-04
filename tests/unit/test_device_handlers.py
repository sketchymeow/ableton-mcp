import pytest

from AbletonMCP.core.registry import CommandError, Registry
from AbletonMCP.handlers import register_all

from .fake_live import default_song


@pytest.fixture
def song():
    return default_song()


@pytest.fixture
def registry(song):
    registry = Registry()
    register_all(registry, {"song": lambda: song})
    return registry


def test_get_devices(registry):
    result = registry.dispatch("get_devices", {"track_index": 0})
    assert result["devices"][0]["name"] == "Reverb"
    assert result["devices"][0]["path"] == "song.tracks[0].devices[0]"
    assert result["devices"][0]["num_parameters"] == 3


def test_get_devices_rack_recursion(registry):
    result = registry.dispatch("get_devices", {"track_index": 1})
    rack = result["devices"][0]
    assert rack["name"] == "Bass Rack"
    nested = rack["chains"][0]["devices"][0]
    assert nested["name"] == "Operator"
    assert nested["path"] == "song.tracks[1].devices[0].chains[0].devices[0]"


def test_get_device_parameters(registry):
    result = registry.dispatch(
        "get_device_parameters", {"track_index": 0, "device_index": 0}
    )
    names = [p["name"] for p in result["parameters"]]
    assert names == ["Device On", "Dry/Wet", "Mode"]
    mode = result["parameters"][2]
    assert mode["is_quantized"] is True
    assert mode["value_items"] == ["Low", "Mid", "High"]


def test_set_parameter_by_name(registry, song):
    result = registry.dispatch(
        "set_device_parameter",
        {"track_index": 0, "device_index": 0, "parameter": "dry/wet", "value": 0.8},
    )
    assert song.tracks[0].devices[0].parameters[1].value == 0.8
    assert result["value"] == 0.8


def test_set_parameter_by_index_int_coerced(registry, song):
    registry.dispatch(
        "set_device_parameter",
        {"track_index": 0, "device_index": 0, "parameter": 1, "value": 1},
    )
    assert song.tracks[0].devices[0].parameters[1].value == 1.0


def test_set_quantized_parameter_by_option_name(registry, song):
    result = registry.dispatch(
        "set_device_parameter",
        {"track_index": 0, "device_index": 0, "parameter": "Mode", "value": "high"},
    )
    assert song.tracks[0].devices[0].parameters[2].value == 2.0
    assert result["display"] == "High"


def test_set_quantized_bad_option(registry):
    with pytest.raises(CommandError, match="options: Low, Mid, High"):
        registry.dispatch(
            "set_device_parameter",
            {"track_index": 0, "device_index": 0, "parameter": "Mode",
             "value": "Extreme"},
        )


def test_set_parameter_unknown_name(registry):
    with pytest.raises(CommandError, match="no parameter named"):
        registry.dispatch(
            "set_device_parameter",
            {"track_index": 0, "device_index": 0, "parameter": "Cutoff", "value": 1.0},
        )


def test_delete_device(registry, song):
    result = registry.dispatch("delete_device", {"track_index": 0, "device_index": 0})
    assert result["deleted"] == "Reverb"
    assert len(song.tracks[0].devices) == 0


def test_device_index_out_of_range(registry):
    with pytest.raises(CommandError, match="out of range"):
        registry.dispatch(
            "get_device_parameters", {"track_index": 0, "device_index": 5}
        )
