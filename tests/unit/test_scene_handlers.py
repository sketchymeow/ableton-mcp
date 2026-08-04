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


def test_create_scene_appends(registry, song):
    result = registry.dispatch("create_scene", {})
    assert result["index"] == 2
    assert len(song.scenes) == 3


def test_create_scene_at_index(registry, song):
    result = registry.dispatch("create_scene", {"index": 0})
    assert result["index"] == 0
    assert song.scenes[1].name == "Intro"


def test_delete_scene(registry, song):
    registry.dispatch("delete_scene", {"index": 0})
    assert [s.name for s in song.scenes] == ["Drop"]


def test_delete_scene_out_of_range(registry):
    with pytest.raises(CommandError, match="out of range"):
        registry.dispatch("delete_scene", {"index": 5})


def test_duplicate_scene(registry, song):
    result = registry.dispatch("duplicate_scene", {"index": 0})
    assert result["index"] == 1
    assert song.scenes[1].name == "Intro"
    assert len(song.scenes) == 3


def test_fire_scene(registry, song):
    registry.dispatch("fire_scene", {"index": 1})
    assert song.scenes[1].fired == 1


def test_set_scene(registry, song):
    result = registry.dispatch(
        "set_scene", {"index": 0, "name": "Buildup", "tempo": 128.0}
    )
    assert song.scenes[0].name == "Buildup"
    assert song.scenes[0].tempo == 128.0
    assert result["tempo"] == 128.0


def test_set_scene_rejects_unknown(registry):
    with pytest.raises(CommandError, match="cannot set fired"):
        registry.dispatch("set_scene", {"index": 0, "fired": 1})
