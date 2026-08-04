#!/usr/bin/env python3
"""Install the AbletonMCP remote script into Live's User Library.

Copies remote_script/AbletonMCP into the Remote Scripts folder so Live
lists it as a control surface. Use --symlink during development so edits
apply on the next Live restart without reinstalling.
"""

import argparse
import platform
import shutil
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "remote_script" / "AbletonMCP"


def default_dest() -> Path | None:
    home = Path.home()
    system = platform.system()
    if system == "Darwin":
        return home / "Music" / "Ableton" / "User Library" / "Remote Scripts"
    if system == "Windows":
        return home / "Documents" / "Ableton" / "User Library" / "Remote Scripts"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dest",
        type=Path,
        default=None,
        help="Remote Scripts folder (default: Live's User Library for this OS)",
    )
    parser.add_argument(
        "--symlink",
        action="store_true",
        help="symlink instead of copy, so source edits apply on Live restart",
    )
    args = parser.parse_args()

    dest = args.dest or default_dest()
    if dest is None:
        print("Could not guess the Remote Scripts folder on this OS; pass --dest.")
        return 1

    dest.mkdir(parents=True, exist_ok=True)
    target = dest / "AbletonMCP"
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.is_dir():
        shutil.rmtree(target)

    if args.symlink:
        target.symlink_to(SOURCE, target_is_directory=True)
        print(f"Symlinked {target} -> {SOURCE}")
    else:
        shutil.copytree(
            SOURCE, target,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "logs"),
        )
        print(f"Copied {SOURCE} -> {target}")

    repo = SOURCE.parents[1]
    print(
        "\nNext steps:\n"
        "  1. Restart Ableton Live.\n"
        "  2. Settings > Link, Tempo & MIDI > Control Surface > AbletonMCP.\n"
        "  3. Look for 'AbletonMCP: listening on 127.0.0.1:9877' in Live's "
        "status bar.\n"
        "  4. Add the server to your MCP client config:\n\n"
        '     {\n'
        '       "mcpServers": {\n'
        '         "ableton-live": {\n'
        '           "command": "uv",\n'
        f'           "args": ["run", "--directory", "{repo}", "ableton-mcp"]\n'
        "         }\n"
        "       }\n"
        "     }"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
