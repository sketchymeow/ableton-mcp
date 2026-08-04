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


def test_create_clip(registry, song):
    result = registry.dispatch(
        "create_clip", {"track_index": 0, "scene_index": 0, "length": 8.0}
    )
    assert result["length"] == 8.0
    assert song.tracks[0].clip_slots[0].has_clip


def test_create_clip_occupied(registry):
    registry.dispatch("create_clip", {"track_index": 0, "scene_index": 0})
    with pytest.raises(CommandError, match="already has a clip"):
        registry.dispatch("create_clip", {"track_index": 0, "scene_index": 0})


def test_delete_clip(registry, song):
    registry.dispatch("create_clip", {"track_index": 0, "scene_index": 0})
    registry.dispatch("delete_clip", {"track_index": 0, "scene_index": 0})
    assert not song.tracks[0].clip_slots[0].has_clip


def test_delete_clip_empty_slot(registry):
    with pytest.raises(CommandError, match="no clip"):
        registry.dispatch("delete_clip", {"track_index": 0, "scene_index": 0})


def test_fire_and_stop(registry, song):
    registry.dispatch("fire_clip", {"track_index": 0, "scene_index": 1})
    registry.dispatch("stop_clip", {"track_index": 0, "scene_index": 1})
    slot = song.tracks[0].clip_slots[1]
    assert slot.fired == 1
    assert slot.stopped == 1


def test_get_clip_missing(registry):
    with pytest.raises(CommandError, match="no clip at track"):
        registry.dispatch("get_clip", {"track_index": 0, "scene_index": 0})


def test_set_clip(registry, song):
    registry.dispatch("create_clip", {"track_index": 0, "scene_index": 0})
    result = registry.dispatch(
        "set_clip",
        {"track_index": 0, "scene_index": 0, "name": "Beat", "looping": False,
         "loop_end": 16, "color": "#00FF00"},
    )
    clip = song.tracks[0].clip_slots[0].clip
    assert clip.name == "Beat"
    assert clip.looping is False
    assert clip.loop_end == 16.0
    assert result["name"] == "Beat"
    assert result["color"] == "#00FF00"


def test_set_clip_rejects_unknown(registry):
    registry.dispatch("create_clip", {"track_index": 0, "scene_index": 0})
    with pytest.raises(CommandError, match="cannot set is_playing"):
        registry.dispatch(
            "set_clip", {"track_index": 0, "scene_index": 0, "is_playing": True}
        )


def test_clip_to_arrangement(registry, song):
    registry.dispatch("create_clip", {"track_index": 0, "scene_index": 0})
    registry.dispatch(
        "clip_to_arrangement", {"track_index": 0, "scene_index": 0, "time": 32.0}
    )
    clips = registry.dispatch("get_arrangement_clips", {"track_index": 0})["clips"]
    assert len(clips) == 1
    assert clips[0]["start_time"] == 32.0
    assert clips[0]["clip_index"] == 0


def test_delete_arrangement_clip(registry, song):
    registry.dispatch("create_clip", {"track_index": 0, "scene_index": 0})
    registry.dispatch(
        "clip_to_arrangement", {"track_index": 0, "scene_index": 0, "time": 0.0}
    )
    registry.dispatch(
        "delete_clip", {"track_index": 0, "location": "arrangement", "clip_index": 0}
    )
    assert len(song.tracks[0].arrangement_clips) == 0
