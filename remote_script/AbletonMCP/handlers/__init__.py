from . import (automation, browser, clip, device, events, mixer, notes, raw,
               scene, song, track)


def register_all(registry, roots):
    browser.register(registry, roots)
    events.register(registry, roots)
    raw.register(registry, roots)
    song.register(registry, roots)
    track.register(registry, roots)
    scene.register(registry, roots)
    clip.register(registry, roots)
    notes.register(registry, roots)
    mixer.register(registry, roots)
    device.register(registry, roots)
    automation.register(registry, roots)
