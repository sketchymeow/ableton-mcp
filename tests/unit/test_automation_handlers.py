import pytest

from AbletonMCP.core.registry import CommandError, Registry
from AbletonMCP.handlers import register_all

from .fake_live import default_song

CLIP = {"track_index": 0, "scene_index": 0}
DRYWET = dict(CLIP, device_index=0, parameter="Dry/Wet")


@pytest.fixture
def song():
    return default_song()


@pytest.fixture
def registry(song):
    registry = Registry()
    register_all(registry, {"song": lambda: song})
    registry.dispatch("create_clip", dict(CLIP, length=8.0))
    return registry


def sweep(registry, **extra):
    return registry.dispatch(
        "write_automation",
        dict(DRYWET, points=[
            {"time": 0.0, "value": 0.0},
            {"time": 4.0, "value": 0.5},
            {"time": 8.0, "value": 1.0},
        ], **extra),
    )


def test_write_and_read_device_automation(registry):
    result = sweep(registry)
    assert result["written"] == 3
    assert result["parameter"] == "Dry/Wet"
    read = registry.dispatch(
        "read_automation", dict(DRYWET, times=[0.0, 4.0, 6.0, 8.0])
    )
    assert read["has_envelope"] is True
    values = [p["value"] for p in read["points"]]
    assert values == [0.0, 0.5, 0.5, 1.0]


def test_read_without_envelope(registry):
    read = registry.dispatch("read_automation", DRYWET)
    assert read == {"has_envelope": False, "points": []}


def test_read_sampled(registry):
    sweep(registry)
    read = registry.dispatch("read_automation", dict(DRYWET, samples=5))
    times = [p["time"] for p in read["points"]]
    assert times == [0.0, 2.0, 4.0, 6.0, 8.0]


def test_mixer_automation(registry, song):
    registry.dispatch(
        "write_automation",
        dict(CLIP, mixer_parameter="volume",
             points=[{"time": 0.0, "value": 0.2}]),
    )
    clip = song.tracks[0].clip_slots[0].clip
    volume = song.tracks[0].mixer_device.volume
    assert clip.automation_envelope(volume).steps == [(0.0, 0.0, 0.2)]


def test_send_automation(registry, song):
    registry.dispatch(
        "write_automation",
        dict(CLIP, mixer_parameter="send", send_index=0,
             points=[{"time": 1.0, "value": 0.9, "length": 2.0}]),
    )
    send = song.tracks[0].mixer_device.sends[0]
    clip = song.tracks[0].clip_slots[0].clip
    assert clip.automation_envelope(send).steps == [(1.0, 2.0, 0.9)]


def test_clear_first_replaces(registry, song):
    sweep(registry)
    sweep(registry, clear_first=True)
    clip = song.tracks[0].clip_slots[0].clip
    param = song.tracks[0].devices[0].parameters[1]
    assert len(clip.automation_envelope(param).steps) == 3


def test_clear_one_parameter(registry, song):
    sweep(registry)
    registry.dispatch("clear_automation", DRYWET)
    clip = song.tracks[0].clip_slots[0].clip
    param = song.tracks[0].devices[0].parameters[1]
    assert clip.automation_envelope(param) is None


def test_clear_all(registry, song):
    sweep(registry)
    result = registry.dispatch("clear_automation", CLIP)
    assert result == {"cleared": "all"}
    assert song.tracks[0].clip_slots[0].clip._envelopes == {}


def test_missing_target(registry):
    with pytest.raises(CommandError, match="specify a target"):
        registry.dispatch(
            "write_automation", dict(CLIP, points=[{"time": 0, "value": 0}])
        )


def test_bad_mixer_parameter(registry):
    with pytest.raises(CommandError, match="mixer_parameter must be"):
        registry.dispatch(
            "write_automation",
            dict(CLIP, mixer_parameter="widener",
                 points=[{"time": 0, "value": 0}]),
        )
