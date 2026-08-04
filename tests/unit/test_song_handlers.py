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


def test_song_status(registry):
    status = registry.dispatch("get_song_status", {})
    assert status["tempo"] == 120.0
    assert status["signature"] == "4/4"
    assert status["loop"] == {"on": False, "start": 0.0, "length": 4.0}
    assert status["num_tracks"] == 2
    assert status["num_scenes"] == 2
    assert status["num_returns"] == 1


def test_set_song(registry, song):
    status = registry.dispatch("set_song", {"tempo": 90, "metronome": True})
    assert song.tempo == 90.0
    assert song.metronome is True
    assert status["tempo"] == 90.0


def test_set_song_rejects_unknown(registry):
    with pytest.raises(CommandError, match="cannot set is_playing"):
        registry.dispatch("set_song", {"is_playing": True})


def test_get_tracks(registry):
    result = registry.dispatch("get_tracks", {})
    assert [t["name"] for t in result["tracks"]] == ["Drums", "Bass"]
    assert result["tracks"][0]["type"] == "midi"
    assert result["tracks"][0]["devices"] == ["Reverb"]
    assert result["returns"][0]["name"] == "A Reverb"
    assert result["master"]["type"] == "master"
    assert "arm" not in result["master"]


def test_get_scenes(registry):
    result = registry.dispatch("get_scenes", {})
    assert [s["name"] for s in result["scenes"]] == ["Intro", "Drop"]
    assert "tempo" not in result["scenes"][0]  # -1 means unset
    assert result["scenes"][1]["tempo"] == 140.0


def test_get_cue_points(registry):
    result = registry.dispatch("get_cue_points", {})
    assert [c["name"] for c in result["cue_points"]] == ["Verse", "Chorus"]
