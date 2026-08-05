"""Install the AbletonMCP remote script into Live's User Library.

Used by scripts/install_remote_script.py (CLI) and the install_remote_script
MCP tool, including from inside a PyInstaller binary.
"""

import platform
import shutil
import sys
from pathlib import Path


class InstallError(Exception):
    pass


def remote_script_source() -> Path:
    # Installed wheel or PyInstaller bundle: data ships inside the package.
    packaged = Path(__file__).resolve().parent / "remote_script" / "AbletonMCP"
    if packaged.is_dir():
        return packaged
    # Repo checkout (editable install).
    checkout = Path(__file__).resolve().parents[2] / "remote_script" / "AbletonMCP"
    if checkout.is_dir():
        return checkout
    raise InstallError("could not locate the bundled remote script")


def default_dest() -> Path | None:
    home = Path.home()
    system = platform.system()
    if system == "Darwin":
        return home / "Music" / "Ableton" / "User Library" / "Remote Scripts"
    if system == "Windows":
        return home / "Documents" / "Ableton" / "User Library" / "Remote Scripts"
    return None


def install(dest: Path | None = None, symlink: bool = False) -> dict:
    """Copy (or symlink) the remote script into the Remote Scripts folder.

    Returns a dict describing what happened, for both CLI output and the
    MCP tool result.
    """
    source = remote_script_source()
    if symlink and getattr(sys, "frozen", False):
        raise InstallError(
            "symlink install isn't available from the packaged app; the "
            "bundled source is temporary. Use a git checkout for that."
        )
    dest = dest or default_dest()
    if dest is None:
        raise InstallError(
            "could not guess the Remote Scripts folder on this OS; pass an "
            "explicit destination"
        )
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / "AbletonMCP"
    replaced = target.exists() or target.is_symlink()
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.is_dir():
        shutil.rmtree(target)

    if symlink:
        target.symlink_to(source, target_is_directory=True)
    else:
        shutil.copytree(
            source, target,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "logs"),
        )
    return {
        "installed_to": str(target),
        "mode": "symlink" if symlink else "copy",
        "replaced_existing": replaced,
        "next_steps": [
            "Restart Ableton Live.",
            "Settings > Link, Tempo & MIDI > Control Surface > AbletonMCP.",
            "Look for 'AbletonMCP: listening on 127.0.0.1:9877' in Live's "
            "status bar.",
        ],
    }
