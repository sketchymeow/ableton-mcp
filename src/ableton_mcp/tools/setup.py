"""First-run setup: install the remote script from inside the MCP server."""

from pathlib import Path

from ..installer import InstallError, default_dest, install


def register(mcp):
    @mcp.tool()
    def install_remote_script(dest: str | None = None) -> dict:
        """Install the AbletonMCP control surface into Ableton Live's User
        Library. Call this when ping can't reach Live and the user hasn't
        set the remote script up yet (or needs it updated). The user must
        restart Live afterwards - tell them the next_steps."""
        try:
            return install(dest=Path(dest) if dest else None)
        except InstallError as exc:
            return {"error": str(exc)}

    @mcp.tool()
    def remote_script_status() -> dict:
        """Check whether the AbletonMCP remote script is installed in Live's
        User Library (this says nothing about whether Live is running - use
        ping for that)."""
        dest = default_dest()
        if dest is None:
            return {"installed": False, "reason": "unsupported OS; pass an explicit dest to install_remote_script"}
        target = dest / "AbletonMCP"
        return {
            "installed": target.exists(),
            "path": str(target),
            "is_symlink": target.is_symlink(),
        }
