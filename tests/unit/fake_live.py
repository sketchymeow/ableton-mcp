"""Minimal stand-ins for Live Object Model objects, for tests without Live."""


class FakeVector(tuple):
    pass


class FakeDeviceParameter:
    def __init__(self, name, value=0.0, min=0.0, max=1.0):
        self.name = name
        self.value = value
        self.min = min
        self.max = max

    def __setattr__(self, key, value):
        # Live rejects ints for float parameters; mimic that strictness.
        if key == "value" and type(value) is int:
            raise TypeError("expected float, got int")
        object.__setattr__(self, key, value)

    def add_value_listener(self, callback):
        pass

    def remove_value_listener(self, callback):
        pass


class FakeDevice:
    def __init__(self, name, parameters=()):
        self.name = name
        self.class_name = "Fake%s" % name
        self.parameters = FakeVector(parameters)


class FakeTrack:
    def __init__(self, name, devices=()):
        self.name = name
        self.mute = False
        self.devices = FakeVector(devices)


class FakeSong:
    def __init__(self, tracks=()):
        self.tempo = 120.0
        self.is_playing = False
        self.tracks = FakeVector(tracks)
        self.started = 0

    def start_playing(self):
        self.started += 1
        self.is_playing = True

    def create_midi_track(self, index):
        track = FakeTrack("MIDI %d" % len(self.tracks))
        self.tracks = FakeVector(tuple(self.tracks) + (track,))
        return track

    def add_tempo_listener(self, callback):
        pass

    def remove_tempo_listener(self, callback):
        pass


def default_song():
    return FakeSong(
        tracks=(
            FakeTrack(
                "Drums",
                devices=(
                    FakeDevice(
                        "Reverb",
                        parameters=(
                            FakeDeviceParameter("Device On", 1.0),
                            FakeDeviceParameter("Dry/Wet", 0.5),
                        ),
                    ),
                ),
            ),
            FakeTrack("Bass"),
        )
    )
