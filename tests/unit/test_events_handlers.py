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


def test_subscribe_emits_baseline(registry):
    registry.dispatch("subscribe", {"path": "song", "property": "tempo"})
    result = registry.dispatch("poll_events", {})
    assert len(result["events"]) == 1
    assert result["events"][0]["value"] == 120.0
    assert result["subscriptions"] == [{"path": "song", "property": "tempo"}]


def test_change_events_and_cursor(registry, song):
    registry.dispatch("subscribe", {"path": "song", "property": "tempo"})
    cursor = registry.dispatch("poll_events", {})["last_seq"]
    song.tempo = 90.0
    song.fire_tempo_listeners()
    song.tempo = 100.0
    song.fire_tempo_listeners()
    result = registry.dispatch("poll_events", {"since": cursor})
    assert [e["value"] for e in result["events"]] == [90.0, 100.0]
    again = registry.dispatch("poll_events", {"since": result["last_seq"]})
    assert again["events"] == []


def test_subscribe_parameter_value(registry, song):
    registry.dispatch(
        "subscribe",
        {"path": "song.tracks[0].devices[0].parameters[1]", "property": "value"},
    )
    param = song.tracks[0].devices[0].parameters[1]
    param.value = 0.9
    param.fire_value_listeners()
    result = registry.dispatch("poll_events", {})
    assert result["events"][-1]["value"] == 0.9


def test_resubscribe_replaces(registry, song):
    registry.dispatch("subscribe", {"path": "song", "property": "tempo"})
    registry.dispatch("subscribe", {"path": "song", "property": "tempo"})
    assert len(song._tempo_listeners) == 1


def test_unsubscribe(registry, song):
    registry.dispatch("subscribe", {"path": "song", "property": "tempo"})
    result = registry.dispatch(
        "unsubscribe", {"path": "song", "property": "tempo"}
    )
    assert result == {"removed": 1}
    assert song._tempo_listeners == []
    song.fire_tempo_listeners()  # no listeners left, nothing should blow up


def test_unsubscribe_all(registry, song):
    registry.dispatch("subscribe", {"path": "song", "property": "tempo"})
    registry.dispatch(
        "subscribe",
        {"path": "song.tracks[0].devices[0].parameters[1]", "property": "value"},
    )
    result = registry.dispatch("unsubscribe", {})
    assert result == {"removed": 2}
    assert registry.dispatch("poll_events", {})["subscriptions"] == []


def test_unsubscribe_unknown(registry):
    with pytest.raises(CommandError, match="no subscription"):
        registry.dispatch("unsubscribe", {"path": "song", "property": "tempo"})


def test_subscribe_not_listenable(registry):
    with pytest.raises(CommandError, match="not listenable"):
        registry.dispatch("subscribe", {"path": "song", "property": "song_length"})
