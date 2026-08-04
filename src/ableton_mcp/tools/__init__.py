from . import clips, devices, mixer, notes, raw, scenes, song, tracks


def register_all(mcp):
    raw.register(mcp)
    song.register(mcp)
    tracks.register(mcp)
    scenes.register(mcp)
    clips.register(mcp)
    notes.register(mcp)
    mixer.register(mcp)
    devices.register(mcp)
