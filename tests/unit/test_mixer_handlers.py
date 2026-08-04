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


def test_get_mixer(registry):
    result = registry.dispatch("get_mixer", {"track_index": 0})
    assert result["volume"]["value"] == 0.85
    assert result["volume"]["display"] == "0.85 x"
    assert result["sends"][0]["name"] == "A Reverb"
    assert result["crossfade_assign"] == "none"


def test_get_master_mixer(registry):
    result = registry.dispatch("get_mixer", {"track_type": "master"})
    assert "cue_volume" in result
    assert "crossfader" in result


def test_set_mixer(registry, song):
    result = registry.dispatch(
        "set_mixer", {"track_index": 0, "volume": 0.5, "panning": -0.3,
                      "crossfade_assign": "A"}
    )
    mixer = song.tracks[0].mixer_device
    assert mixer.volume.value == 0.5
    assert mixer.panning.value == -0.3
    assert mixer.crossfade_assign == 0
    assert result["volume"]["value"] == 0.5


def test_set_mixer_int_coerced(registry, song):
    registry.dispatch("set_mixer", {"track_index": 0, "volume": 1})
    assert song.tracks[0].mixer_device.volume.value == 1.0


def test_set_mixer_bad_crossfade(registry):
    with pytest.raises(CommandError, match="crossfade_assign"):
        registry.dispatch("set_mixer", {"track_index": 0, "crossfade_assign": "C"})


def test_set_mixer_nothing(registry):
    with pytest.raises(CommandError, match="nothing to set"):
        registry.dispatch("set_mixer", {"track_index": 0})


def test_set_send(registry, song):
    result = registry.dispatch(
        "set_send", {"track_index": 0, "send_index": 0, "value": 0.7}
    )
    assert song.tracks[0].mixer_device.sends[0].value == 0.7
    assert result["index"] == 0


def test_set_send_out_of_range(registry):
    with pytest.raises(CommandError, match="out of range"):
        registry.dispatch("set_send", {"track_index": 0, "send_index": 5, "value": 0.5})
