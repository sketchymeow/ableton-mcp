from . import raw, scenes, song, tracks


def register_all(mcp):
    raw.register(mcp)
    song.register(mcp)
    tracks.register(mcp)
    scenes.register(mcp)
