"""MCP server exposing Ableton Live over the remote script bridge."""

from mcp.server import MCPServer

from .tools import register_all

mcp = MCPServer("ableton-live")
register_all(mcp)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
