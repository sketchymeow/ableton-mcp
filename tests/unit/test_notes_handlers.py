import pytest

from AbletonMCP.core.registry import CommandError, Registry
from AbletonMCP.handlers import register_all

from .fake_live import default_song, install_fake_live_module

install_fake_live_module()

CLIP = {"track_index": 0, "scene_index": 0}


@pytest.fixture
def song():
    return default_song()


@pytest.fixture
def registry(song):
    registry = Registry()
    register_all(registry, {"song": lambda: song})
    registry.dispatch("create_clip", dict(CLIP, length=4.0))
    return registry


def add_triad(registry):
    return registry.dispatch(
        "add_notes",
        dict(CLIP, notes=[
            {"pitch": 60, "start_time": 0.0, "duration": 1.0},
            {"pitch": 64, "start_time": 0.0, "duration": 1.0, "velocity": 80},
            {"pitch": 67, "start_time": 2.0, "duration": 0.5, "mute": True},
        ]),
    )


def test_add_and_get_notes(registry):
    result = add_triad(registry)
    assert result["added"] == 3
    notes = registry.dispatch("get_notes", CLIP)["notes"]
    assert [n["pitch"] for n in notes] == [60, 64, 67]
    assert notes[1]["velocity"] == 80
    assert notes[2]["mute"] is True
    assert all(n["note_id"] for n in notes)


def test_get_notes_range_filter(registry):
    add_triad(registry)
    notes = registry.dispatch(
        "get_notes", dict(CLIP, from_time=0.0, time_span=1.0)
    )["notes"]
    assert [n["pitch"] for n in notes] == [60, 64]
    notes = registry.dispatch(
        "get_notes", dict(CLIP, from_pitch=64, pitch_span=1)
    )["notes"]
    assert [n["pitch"] for n in notes] == [64]


def test_update_notes_by_id(registry, song):
    add_triad(registry)
    notes = registry.dispatch("get_notes", CLIP)["notes"]
    target = notes[0]["note_id"]
    result = registry.dispatch(
        "update_notes",
        dict(CLIP, notes=[{"note_id": target, "pitch": 62, "velocity": 50}]),
    )
    assert result["updated"] == 1
    clip = song.tracks[0].clip_slots[0].clip
    assert clip._notes[0].pitch == 62
    assert clip._notes[0].velocity == 50
    assert clip.modifications_applied == 1


def test_update_unknown_id(registry):
    add_triad(registry)
    with pytest.raises(CommandError, match="no note with id 999"):
        registry.dispatch("update_notes", dict(CLIP, notes=[{"note_id": 999}]))


def test_remove_notes_by_id(registry):
    add_triad(registry)
    notes = registry.dispatch("get_notes", CLIP)["notes"]
    registry.dispatch("remove_notes", dict(CLIP, note_ids=[notes[0]["note_id"]]))
    remaining = registry.dispatch("get_notes", CLIP)["notes"]
    assert [n["pitch"] for n in remaining] == [64, 67]


def test_remove_notes_by_range(registry):
    add_triad(registry)
    registry.dispatch("remove_notes", dict(CLIP, from_time=0.0, time_span=1.0))
    remaining = registry.dispatch("get_notes", CLIP)["notes"]
    assert [n["pitch"] for n in remaining] == [67]


def test_add_notes_validation(registry):
    with pytest.raises(CommandError, match="missing: duration"):
        registry.dispatch(
            "add_notes", dict(CLIP, notes=[{"pitch": 60, "start_time": 0.0}])
        )
    with pytest.raises(CommandError, match="non-empty list"):
        registry.dispatch("add_notes", dict(CLIP, notes=[]))


def test_notes_require_midi_clip(registry, song):
    slot = song.tracks[1].clip_slots[0]
    slot.create_clip(4.0)
    slot.clip.is_midi_clip = False
    with pytest.raises(CommandError, match="not a MIDI clip"):
        registry.dispatch("get_notes", {"track_index": 1, "scene_index": 0})
