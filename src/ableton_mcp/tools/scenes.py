"""Scene listing, CRUD, and firing."""

from typing import Literal

from ..connection import get_connection


def register(mcp):
    @mcp.tool()
    def list_scenes() -> dict:
        """List all scenes with name, color, tempo (if set), and trigger
        state."""
        return get_connection().request("get_scenes")

    @mcp.tool()
    def scene(
        action: Literal["create", "delete", "duplicate", "fire"], index: int = -1
    ) -> dict:
        """Create, delete, duplicate, or fire a scene. "create" with index -1
        appends at the end; the other actions need a real index. Firing a
        scene launches every clip in that row."""
        conn = get_connection()
        if action == "create":
            return conn.request("create_scene", {"index": index})
        if index < 0:
            raise ValueError(f"{action} needs a scene index")
        return conn.request(f"{action}_scene", {"index": index})

    @mcp.tool()
    def set_scene(
        index: int,
        name: str | None = None,
        color: str | None = None,
        tempo: float | None = None,
    ) -> dict:
        """Set scene properties in one call. Only the arguments you pass are
        changed. color is "#RRGGBB"."""
        params = {k: v for k, v in locals().items() if v is not None and k != "index"}
        params["index"] = index
        return get_connection().request("set_scene", params)
