import pytest

from AbletonMCP.core.registry import CommandError, Registry
from AbletonMCP.handlers import register_all

from .fake_live import FakeApp, default_song


@pytest.fixture
def song():
    return default_song()


@pytest.fixture
def app():
    return FakeApp()


@pytest.fixture
def registry(song, app):
    registry = Registry()
    register_all(registry, {"song": lambda: song, "app": lambda: app})
    return registry


def test_browse_root(registry):
    result = registry.dispatch("browse", {"root": "instruments"})
    assert result["path"] == ["Instruments"]
    assert result["total"] == 2
    assert [i["name"] for i in result["items"]] == ["Operator", "Analog"]
    assert result["items"][1]["uri"] == "device:analog"


def test_browse_paging(registry):
    result = registry.dispatch(
        "browse", {"root": "instruments", "offset": 1, "limit": 1}
    )
    assert result["total"] == 2
    assert result["offset"] == 1
    assert [i["name"] for i in result["items"]] == ["Analog"]
    assert result["items"][0]["index"] == 1


def test_browse_limit_clamped(registry):
    result = registry.dispatch(
        "browse", {"root": "instruments", "limit": 100000}
    )
    assert len(result["items"]) == 2  # clamp applies, small tree unaffected


def test_search_max_results_clamped(registry):
    # A huge max_results must not produce an unbounded payload.
    result = registry.dispatch(
        "search_browser", {"query": "a", "max_results": 100000}
    )
    assert len(result["matches"]) <= 100


def test_browse_by_name_path(registry):
    result = registry.dispatch("browse", {"root": "instruments", "path": ["operator"]})
    assert [i["name"] for i in result["items"]] == ["Growl Bass"]
    assert result["total"] == 1


def test_browse_by_index_path(registry):
    result = registry.dispatch("browse", {"root": "instruments", "path": [0]})
    assert result["items"][0]["uri"] == "preset:growl"


def test_browse_bad_name(registry):
    with pytest.raises(CommandError, match="no item named 'Wavetable'"):
        registry.dispatch("browse", {"root": "instruments", "path": ["Wavetable"]})


def test_browse_user_folders(registry):
    # Places: browser.user_folders is a vector of roots, one per folder.
    result = registry.dispatch("browse", {"root": "user_folders"})
    assert result["path"] == ["Places"]
    assert [i["name"] for i in result["items"]] == ["My Samples"]
    nested = registry.dispatch(
        "browse", {"root": "user_folders", "path": ["My Samples"]}
    )
    assert nested["items"][0]["uri"] == "userfile:kick01"


def test_search_user_folders(registry):
    result = registry.dispatch(
        "search_browser", {"query": "kick", "roots": ["user_folders"]}
    )
    assert [m["name"] for m in result["matches"]] == ["kick_01.wav"]


def test_browse_bad_root(registry):
    with pytest.raises(CommandError, match="unknown root"):
        registry.dispatch("browse", {"root": "vsts"})


def test_search(registry):
    result = registry.dispatch("search_browser", {"query": "rev"})
    assert [m["name"] for m in result["matches"]] == ["Reverb"]
    assert result["matches"][0]["path"] == "audio_effects > Reverb"
    assert result["truncated"] is False


def test_search_max_results(registry):
    result = registry.dispatch("search_browser", {"query": "a", "max_results": 1})
    assert len(result["matches"]) == 1


def test_load_from_search_cache(registry, app, song):
    registry.dispatch("search_browser", {"query": "analog"})
    result = registry.dispatch(
        "load_browser_item", {"uri": "device:analog", "track_index": 1}
    )
    assert result["loaded"] == "Analog"
    assert app.browser.loaded[0].uri == "device:analog"
    assert song.view.selected_track is song.tracks[1]


def test_load_without_cache_walks_tree(registry, app):
    result = registry.dispatch("load_browser_item", {"uri": "preset:growl"})
    assert result["loaded"] == "Growl Bass"
    assert app.browser.loaded[0].uri == "preset:growl"


def test_load_unknown_uri(registry):
    with pytest.raises(CommandError, match="no browser item with uri"):
        registry.dispatch("load_browser_item", {"uri": "device:nope"})
