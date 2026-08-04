import pytest

from AbletonMCP.core.lom import LomPathError, describe, resolve, safe_value

from .fake_live import FakeVector, default_song


@pytest.fixture
def roots():
    song = default_song()
    return {"song": lambda: song}


def test_resolve_root(roots):
    assert resolve(roots, "song") is roots["song"]()


def test_resolve_nested_index(roots):
    param = resolve(roots, "song.tracks[0].devices[0].parameters[1]")
    assert param.name == "Dry/Wet"


def test_unknown_root(roots):
    with pytest.raises(LomPathError, match="unknown root"):
        resolve(roots, "nope.tracks[0]")


def test_unknown_attribute(roots):
    with pytest.raises(LomPathError, match="no attribute"):
        resolve(roots, "song.does_not_exist")


def test_index_out_of_range(roots):
    with pytest.raises(LomPathError, match="out of range"):
        resolve(roots, "song.tracks[99]")


def test_bad_segment_syntax(roots):
    with pytest.raises(LomPathError, match="bad path segment"):
        resolve(roots, "song.tracks[x]")


def test_safe_value_primitives():
    assert safe_value(1.5) == 1.5
    assert safe_value("a") == "a"
    assert safe_value(None) is None
    assert safe_value(True) is True


def test_safe_value_vector_of_objects(roots):
    song = roots["song"]()
    values = safe_value(song.tracks)
    assert values == [
        {"__type__": "FakeTrack", "name": "Drums"},
        {"__type__": "FakeTrack", "name": "Bass"},
    ]
    assert isinstance(song.tracks, FakeVector)


def test_describe(roots):
    song = roots["song"]()
    info = describe(song)
    assert info["type"] == "FakeSong"
    assert info["properties"]["tempo"] == 120.0
    assert "create_midi_track" in info["methods"]
    assert "tempo" in info["listenable"]
    assert "add_tempo_listener" not in info["methods"]
