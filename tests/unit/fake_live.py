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


class FakeClip:
    def __init__(self, name="Clip", length=4.0):
        self.name = name
        self.length = length
        self.color = 0xFF0000
        self.is_playing = False


class FakeClipSlot:
    def __init__(self, clip=None):
        self.clip = clip
        self.fired = 0

    @property
    def has_clip(self):
        return self.clip is not None

    def fire(self):
        self.fired += 1


class FakeRoutingType:
    def __init__(self, display_name):
        self.display_name = display_name


class FakeTrack:
    def __init__(self, name, devices=(), has_midi_input=True, is_foldable=False,
                 num_slots=2):
        self.name = name
        self.color = 0x0000FF
        self.arm = False
        self.can_be_armed = True
        self.mute = False
        self.solo = False
        self.is_foldable = is_foldable
        self.fold_state = 0
        self.is_grouped = False
        self.is_visible = True
        self.has_midi_input = has_midi_input
        self.has_audio_input = not has_midi_input
        self.playing_slot_index = -1
        self.fired_slot_index = -1
        self.current_monitoring_state = 1
        self.devices = FakeVector(devices)
        self.clip_slots = FakeVector(FakeClipSlot() for _ in range(num_slots))
        self.available_input_routing_types = FakeVector(
            (FakeRoutingType("Ext. In"), FakeRoutingType("Resampling"))
        )
        self.available_input_routing_channels = FakeVector(
            (FakeRoutingType("1"), FakeRoutingType("1/2"))
        )
        self.available_output_routing_types = FakeVector(
            (FakeRoutingType("Master"), FakeRoutingType("Sends Only"))
        )
        self.available_output_routing_channels = FakeVector(())
        self.input_routing_type = self.available_input_routing_types[0]
        self.input_routing_channel = self.available_input_routing_channels[0]
        self.output_routing_type = self.available_output_routing_types[0]
        self.output_routing_channel = None
        self.stopped = 0

    def stop_all_clips(self):
        self.stopped += 1


class FakeMasterTrack:
    def __init__(self):
        self.name = "Master"
        self.color = 0x808080
        self.can_be_armed = False
        self.mute = False
        self.solo = False
        self.devices = FakeVector(())


class FakeScene:
    def __init__(self, name="", tempo=-1.0):
        self.name = name
        self.color = 0x00FF00
        self.tempo = tempo
        self.is_empty = True
        self.is_triggered = False
        self.fired = 0

    def fire(self):
        self.fired += 1


class FakeCuePoint:
    def __init__(self, name, time):
        self.name = name
        self.time = time
        self.jumped = 0

    def jump(self):
        self.jumped += 1


class FakeSong:
    def __init__(self, tracks=(), scenes=(), return_tracks=(), cue_points=()):
        self.tempo = 120.0
        self.signature_numerator = 4
        self.signature_denominator = 4
        self.is_playing = False
        self.current_song_time = 0.0
        self.song_length = 16.0
        self.loop = False
        self.loop_start = 0.0
        self.loop_length = 4.0
        self.metronome = False
        self.record_mode = 0
        self.session_record = False
        self.can_undo = True
        self.can_redo = False
        self.clip_trigger_quantization = 4
        self.midi_recording_quantization = 0
        self.groove_amount = 0.0
        self.root_note = 0
        self.scale_name = "Major"
        self.tracks = FakeVector(tracks)
        self.scenes = FakeVector(scenes)
        self.return_tracks = FakeVector(return_tracks)
        self.cue_points = FakeVector(cue_points)
        self.master_track = FakeMasterTrack()
        self.started = 0
        self.undone = 0

    def start_playing(self):
        self.started += 1
        self.is_playing = True

    def stop_playing(self):
        self.is_playing = False

    def continue_playing(self):
        self.is_playing = True

    def stop_all_clips(self):
        pass

    def tap_tempo(self):
        pass

    def undo(self):
        self.undone += 1

    def redo(self):
        pass

    def _insert_track(self, index, track):
        tracks = list(self.tracks)
        if index < 0:
            tracks.append(track)
        else:
            tracks.insert(index, track)
        self.tracks = FakeVector(tracks)

    def create_midi_track(self, index):
        track = FakeTrack("MIDI %d" % len(self.tracks), has_midi_input=True)
        self._insert_track(index, track)
        return track

    def create_audio_track(self, index):
        track = FakeTrack("Audio %d" % len(self.tracks), has_midi_input=False)
        self._insert_track(index, track)
        return track

    def create_return_track(self):
        track = FakeTrack("Return %d" % len(self.return_tracks))
        self.return_tracks = FakeVector(tuple(self.return_tracks) + (track,))
        return track

    def delete_track(self, index):
        tracks = list(self.tracks)
        tracks.pop(index)
        self.tracks = FakeVector(tracks)

    def delete_return_track(self, index):
        tracks = list(self.return_tracks)
        tracks.pop(index)
        self.return_tracks = FakeVector(tracks)

    def duplicate_track(self, index):
        source = self.tracks[index]
        copy = FakeTrack(source.name + " Copy",
                         has_midi_input=source.has_midi_input)
        self._insert_track(index + 1, copy)

    def create_scene(self, index):
        scene = FakeScene()
        scenes = list(self.scenes)
        if index < 0:
            scenes.append(scene)
        else:
            scenes.insert(index, scene)
        self.scenes = FakeVector(scenes)
        return scene

    def delete_scene(self, index):
        scenes = list(self.scenes)
        scenes.pop(index)
        self.scenes = FakeVector(scenes)

    def duplicate_scene(self, index):
        source = self.scenes[index]
        scenes = list(self.scenes)
        scenes.insert(index + 1, FakeScene(source.name))
        self.scenes = FakeVector(scenes)

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
        ),
        scenes=(FakeScene("Intro"), FakeScene("Drop", tempo=140.0)),
        return_tracks=(FakeTrack("A Reverb"),),
        cue_points=(FakeCuePoint("Verse", 0.0), FakeCuePoint("Chorus", 16.0)),
    )
