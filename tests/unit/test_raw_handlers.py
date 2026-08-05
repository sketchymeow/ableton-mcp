import pytest

from AbletonMCP.core.registry import CommandError, Registry
from AbletonMCP.handlers import raw

from .fake_live import default_song


@pytest.fixture
def registry():
    song = default_song()
    registry = Registry()
    raw.register(registry, {"song": lambda: song})
    return registry


def test_get_property(registry):
    result = registry.dispatch("get_property", {"path": "song", "property": "tempo"})
    assert result == {"value": 120.0}


def test_get_missing_property(registry):
    with pytest.raises(CommandError, match="no property"):
        registry.dispatch("get_property", {"path": "song", "property": "nope"})


def test_set_property(registry):
    result = registry.dispatch(
        "set_property", {"path": "song", "property": "tempo", "value": 90.5}
    )
    assert result == {"value": 90.5}


def test_set_property_coerces_string_number(registry):
    # MCP clients stringify numbers on union-typed fields; Live's float
    # properties reject strings, so the bridge must parse them.
    result = registry.dispatch(
        "set_property",
        {
            "path": "song.tracks[0].devices[0].parameters[1]",
            "property": "value",
            "value": "0.32",
        },
    )
    assert result == {"value": 0.32}


def test_set_property_garbage_string_on_float(registry):
    with pytest.raises(CommandError, match="expects a number"):
        registry.dispatch(
            "set_property",
            {
                "path": "song.tracks[0].devices[0].parameters[1]",
                "property": "value",
                "value": "loud",
            },
        )


def test_set_routing_property_by_display_name(registry):
    # Object-valued routing property: scalar resolves against available_*.
    result = registry.dispatch(
        "set_property",
        {"path": "song.tracks[0]", "property": "input_routing_type",
         "value": "Resampling"},
    )
    assert result["value"]["name"] == "Resampling"


def test_set_routing_property_by_index(registry):
    result = registry.dispatch(
        "set_property",
        {"path": "song.tracks[0]", "property": "input_routing_type", "value": 1},
    )
    assert result["value"]["name"] == "Resampling"


def test_routing_display_name_beats_digit_index(registry):
    # Channels are named "1", "1/2"; the string "1" must match the name "1"
    # (index 0), not be read as index 1.
    result = registry.dispatch(
        "set_property",
        {"path": "song.tracks[0]", "property": "input_routing_channel",
         "value": "1"},
    )
    assert result["value"]["name"] == "1"


def test_set_routing_property_bad_option(registry):
    with pytest.raises(CommandError, match="options: Ext. In, Resampling"):
        registry.dispatch(
            "set_property",
            {"path": "song.tracks[0]", "property": "input_routing_type",
             "value": "Nope"},
        )


def test_set_object_property_by_value_path(registry):
    result = registry.dispatch(
        "set_property",
        {"path": "song.view", "property": "selected_track",
         "value_path": "song.tracks[1]"},
    )
    assert result["value"]["name"] == "Bass"


def test_set_property_coerces_int_to_float(registry):
    # JSON clients send 1 for 1.0; FakeDeviceParameter rejects ints like Live.
    result = registry.dispatch(
        "set_property",
        {
            "path": "song.tracks[0].devices[0].parameters[1]",
            "property": "value",
            "value": 1,
        },
    )
    assert result == {"value": 1.0}


def test_call_method(registry):
    result = registry.dispatch(
        "call_method", {"path": "song", "method": "create_midi_track", "args": [-1]}
    )
    assert result["result"]["__type__"] == "FakeTrack"
    tracks = registry.dispatch("get_property", {"path": "song", "property": "tracks"})
    assert len(tracks["value"]) == 3


def test_call_property_rejected(registry):
    with pytest.raises(CommandError, match="not a method"):
        registry.dispatch("call_method", {"path": "song", "method": "tempo"})


def test_describe(registry):
    result = registry.dispatch("describe", {"path": "song.tracks[0]"})
    assert result["type"] == "FakeTrack"
    assert "name" in result["properties"]


def test_ping(registry):
    result = registry.dispatch("ping", {})
    assert result["pong"] is True
    assert result["live_version"] is None  # no Live module in tests


def test_unknown_command_lists_valid_ones(registry):
    with pytest.raises(CommandError, match="get_property"):
        registry.dispatch("bogus", {})


def test_missing_param(registry):
    with pytest.raises(CommandError, match="missing param"):
        registry.dispatch("get_property", {"path": "song"})
