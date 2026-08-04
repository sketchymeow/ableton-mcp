from . import clip, device, mixer, notes, raw, scene, song, track


def register_all(registry, roots):
    raw.register(registry, roots)
    song.register(registry, roots)
    track.register(registry, roots)
    scene.register(registry, roots)
    clip.register(registry, roots)
    notes.register(registry, roots)
    mixer.register(registry, roots)
    device.register(registry, roots)
