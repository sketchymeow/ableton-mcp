import pytest

from ableton_mcp import installer


def test_install_copies(tmp_path):
    result = installer.install(dest=tmp_path)
    target = tmp_path / "AbletonMCP"
    assert result["mode"] == "copy"
    assert result["replaced_existing"] is False
    assert (target / "surface.py").is_file()
    assert (target / "core" / "protocol.py").is_file()
    assert not list(target.rglob("__pycache__"))


def test_install_replaces_existing(tmp_path):
    installer.install(dest=tmp_path)
    marker = tmp_path / "AbletonMCP" / "stale.txt"
    marker.write_text("old")
    result = installer.install(dest=tmp_path)
    assert result["replaced_existing"] is True
    assert not marker.exists()


def test_install_symlink(tmp_path):
    result = installer.install(dest=tmp_path, symlink=True)
    target = tmp_path / "AbletonMCP"
    assert result["mode"] == "symlink"
    assert target.is_symlink()
    assert target.resolve() == installer.remote_script_source().resolve()


def test_symlink_rejected_when_frozen(tmp_path, monkeypatch):
    import sys

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    with pytest.raises(installer.InstallError, match="symlink"):
        installer.install(dest=tmp_path, symlink=True)


def test_source_resolves_in_checkout():
    source = installer.remote_script_source()
    assert (source / "__init__.py").is_file()
    assert source.name == "AbletonMCP"
