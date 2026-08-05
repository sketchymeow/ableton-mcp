#!/usr/bin/env python3
"""Build a self-contained .mcpb bundle for Claude Desktop.

Compiles the MCP server (with the remote script as bundled data) into a
single binary with PyInstaller, smoke-tests it over stdio, and zips it
with a manifest into dist/ableton-mcp-<platform>-<arch>.mcpb.

Run from the repo root: uv run python packaging/build_mcpb.py
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

sys.path.insert(0, str(ROOT / "src"))
from ableton_mcp import __version__  # noqa: E402


def binary_name() -> str:
    return "ableton-mcp.exe" if platform.system() == "Windows" else "ableton-mcp"


def build_binary() -> Path:
    data_sep = ";" if platform.system() == "Windows" else ":"
    subprocess.run(
        [
            "pyinstaller",
            "--onefile",
            "--noconfirm",
            "--clean",
            "--log-level", "WARN",
            "--name", "ableton-mcp",
            "--add-data",
            f"{ROOT / 'remote_script' / 'AbletonMCP'}{data_sep}"
            "ableton_mcp/remote_script/AbletonMCP",
            str(ROOT / "packaging" / "entry.py"),
        ],
        check=True,
        cwd=ROOT,
    )
    return DIST / binary_name()


def smoke_test(binary: Path) -> None:
    """The frozen server must answer an MCP initialize over stdio."""
    request = (
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "smoke", "version": "0"},
                },
            }
        )
        + "\n"
    )
    proc = subprocess.run(
        [str(binary)],
        input=request.encode(),
        capture_output=True,
        timeout=60,
    )
    if b'"serverInfo"' not in proc.stdout:
        sys.stderr.write(proc.stderr.decode(errors="replace"))
        raise SystemExit("smoke test failed: no initialize response")
    print("smoke test passed: binary answers MCP initialize")


def manifest() -> dict:
    return {
        "manifest_version": "0.2",
        "name": "ableton-mcp",
        "display_name": "Ableton Live",
        "version": __version__,
        "description": "Control Ableton Live: tracks, clips, MIDI notes, "
        "devices, mixing, automation, and the browser.",
        "author": {"name": "Sketchy Meow"},
        "repository": {
            "type": "git",
            "url": "https://github.com/sketchymeow/ableton-mcp",
        },
        "server": {
            "type": "binary",
            "entry_point": f"server/{binary_name()}",
            "mcp_config": {
                "command": "${__dirname}/server/" + binary_name(),
                "args": [],
            },
        },
        "compatibility": {"platforms": [sys.platform]},
    }


def pack(binary: Path) -> Path:
    arch = platform.machine().lower()
    system = platform.system().lower()
    bundle = DIST / f"ableton-mcp-{system}-{arch}.mcpb"
    bundle.unlink(missing_ok=True)
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest(), indent=2))
        info = zipfile.ZipInfo(f"server/{binary.name}")
        info.external_attr = 0o755 << 16  # keep the binary executable
        zf.writestr(info, binary.read_bytes())
    return bundle


def main() -> None:
    shutil.rmtree(ROOT / "build", ignore_errors=True)
    binary = build_binary()
    smoke_test(binary)
    bundle = pack(binary)
    print(f"built {bundle} ({bundle.stat().st_size // 1024 // 1024} MB)")


if __name__ == "__main__":
    main()
