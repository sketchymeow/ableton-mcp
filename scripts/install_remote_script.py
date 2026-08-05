#!/usr/bin/env python3
"""Install the AbletonMCP remote script into Live's User Library.

Copies remote_script/AbletonMCP into the Remote Scripts folder so Live
lists it as a control surface. Use --symlink during development so edits
apply on the next Live restart without reinstalling.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ableton_mcp.installer import InstallError, install, remote_script_source


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

    try:
        result = install(dest=args.dest, symlink=args.symlink)
    except InstallError as exc:
        print(f"Error: {exc}")
        return 1

    verb = "Symlinked" if result["mode"] == "symlink" else "Copied"
    print(f"{verb} {remote_script_source()} -> {result['installed_to']}")
    print("\nNext steps:")
    for i, step in enumerate(result["next_steps"], 1):
        print(f"  {i}. {step}")

    repo = Path(__file__).resolve().parents[1]
    print(
        "\n  4. Add the server to your MCP client config:\n\n"
        "     {\n"
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
