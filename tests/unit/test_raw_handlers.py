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
