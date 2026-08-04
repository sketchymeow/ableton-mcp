from . import raw, scene, song, track


def register_all(registry, roots):
    raw.register(registry, roots)
    song.register(registry, roots)
    track.register(registry, roots)
    scene.register(registry, roots)
