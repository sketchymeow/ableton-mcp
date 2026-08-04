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


def test_create_midi_track(registry, song):
    result = registry.dispatch("create_track", {"type": "midi"})
    assert result["index"] == 2
    assert result["type"] == "midi"
    assert len(song.tracks) == 3


def test_create_audio_track_at_index(registry, song):
    result = registry.dispatch("create_track", {"type": "audio", "index": 0})
    assert result["index"] == 0
    assert result["type"] == "audio"
    assert song.tracks[0].has_audio_input


def test_create_return_track(registry, song):
    result = registry.dispatch("create_track", {"type": "return"})
    assert result["type"] == "return"
    assert len(song.return_tracks) == 2


def test_create_track_bad_type(registry):
    with pytest.raises(CommandError, match="must be 'midi'"):
        registry.dispatch("create_track", {"type": "instrument"})


def test_delete_track(registry, song):
    registry.dispatch("delete_track", {"track_index": 0})
    assert [t.name for t in song.tracks] == ["Bass"]


def test_delete_return_track(registry, song):
    registry.dispatch("delete_track", {"track_index": 0, "track_type": "return"})
    assert len(song.return_tracks) == 0


def test_delete_master_rejected(registry):
    with pytest.raises(CommandError, match="master"):
        registry.dispatch("delete_track", {"track_index": 0, "track_type": "master"})


def test_delete_out_of_range(registry):
    with pytest.raises(CommandError, match="out of range"):
        registry.dispatch("delete_track", {"track_index": 9})


def test_duplicate_track(registry, song):
    result = registry.dispatch("duplicate_track", {"track_index": 0})
    assert result["index"] == 1
    assert song.tracks[1].name == "Drums Copy"


def test_get_track_detail(registry):
    detail = registry.dispatch("get_track", {"track_index": 0})
    assert detail["name"] == "Drums"
    assert detail["monitoring"] == "auto"
    assert len(detail["clip_slots"]) == 2
    assert detail["routing"]["input_type"] == "Ext. In"
    assert "Resampling" in detail["routing"]["available_input_types"]


def test_set_track(registry, song):
    result = registry.dispatch(
        "set_track",
        {"track_index": 1, "name": "Sub Bass", "color": "#FF8800",
         "mute": True, "monitoring": "off"},
    )
    track = song.tracks[1]
    assert track.name == "Sub Bass"
    assert track.color == 0xFF8800
    assert track.mute is True
    assert track.current_monitoring_state == 2
    assert result["name"] == "Sub Bass"


def test_set_track_rejects_unknown(registry):
    with pytest.raises(CommandError, match="cannot set volume"):
        registry.dispatch("set_track", {"track_index": 0, "volume": 0.5})


def test_set_track_bad_monitoring(registry):
    with pytest.raises(CommandError, match="monitoring"):
        registry.dispatch("set_track", {"track_index": 0, "monitoring": "sideways"})


def test_set_routing(registry, song):
    result = registry.dispatch(
        "set_track_routing", {"track_index": 0, "input_type": "Resampling"}
    )
    assert result["input_type"] == "Resampling"
    assert song.tracks[0].input_routing_type.display_name == "Resampling"


def test_set_routing_unknown_name(registry):
    with pytest.raises(CommandError, match="available: Ext. In, Resampling"):
        registry.dispatch(
            "set_track_routing", {"track_index": 0, "input_type": "Nope"}
        )
