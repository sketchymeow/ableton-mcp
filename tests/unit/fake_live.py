"""Minimal stand-ins for Live Object Model objects, for tests without Live."""


class FakeVector(tuple):
    pass


class FakeDeviceParameter:
    def __init__(self, name, value=0.0, min=0.0, max=1.0, is_quantized=False,
                 value_items=()):
        self.name = name
        self.value = value
        self.min = min
        self.max = max
        self.is_quantized = is_quantized
        self.value_items = FakeVector(value_items)

    def __setattr__(self, key, value):
        # Live rejects ints for float parameters; mimic that strictness.
        if key == "value" and type(value) is int:
            raise TypeError("expected float, got int")
        object.__setattr__(self, key, value)

    def str_for_value(self, value):
        if self.is_quantized and self.value_items:
            return self.value_items[int(value)]
        return "%.2f x" % value

    def add_value_listener(self, callback):
        pass

    def remove_value_listener(self, callback):
        pass


class FakeDevice:
    def __init__(self, name, parameters=()):
        self.name = name
        self.class_name = "Fake%s" % name
        self.type = 1
        self.is_active = True
        self.can_have_chains = False
        self.can_have_drum_pads = False
        self.parameters = FakeVector(parameters)


class FakeChain:
    def __init__(self, name, devices=()):
        self.name = name
        self.devices = FakeVector(devices)


class FakeRackDevice(FakeDevice):
    def __init__(self, name, chains=(), parameters=()):
        FakeDevice.__init__(self, name, parameters)
        self.can_have_chains = True
        self.chains = FakeVector(chains)


class FakeMixerDevice:
    def __init__(self, num_sends=1, is_master=False):
        self.volume = FakeDeviceParameter("Volume", 0.85)
        self.panning = FakeDeviceParameter("Panning", 0.0, -1.0, 1.0)
        self.sends = FakeVector(
            FakeDeviceParameter("Send %d" % i, 0.0) for i in range(num_sends)
        )
        self.crossfade_assign = 1
        if is_master:
            self.cue_volume = FakeDeviceParameter("Cue Volume", 0.85)
            self.crossfader = FakeDeviceParameter("Crossfader", 0.0, -1.0, 1.0)


class FakeMidiNote:
    def __init__(self, note_id, pitch, start_time, duration, velocity=100.0,
                 mute=False, probability=1.0, velocity_deviation=0.0,
                 release_velocity=64.0):
        self.note_id = note_id
        self.pitch = pitch
        self.start_time = start_time
        self.duration = duration
        self.velocity = velocity
        self.mute = mute
        self.probability = probability
        self.velocity_deviation = velocity_deviation
        self.release_velocity = release_velocity


class FakeClip:
    def __init__(self, name="Clip", length=4.0, is_midi=True):
        self.name = name
        self.length = length
        self.color = 0xFF0000
        self.is_playing = False
        self.is_recording = False
        self.is_triggered = False
        self.is_midi_clip = is_midi
        self.is_audio_clip = not is_midi
        self.looping = True
        self.loop_start = 0.0
        self.loop_end = length
        self.start_marker = 0.0
        self.end_marker = length
        self.launch_mode = 0
        self.launch_quantization = 0
        self.legato = False
        self.muted = False
        self.playing_position = 0.0
        self.signature_numerator = 4
        self.signature_denominator = 4
        self.start_time = 0.0
        self.end_time = length
        self._notes = []
        self._next_note_id = 1
        self.modifications_applied = 0

    def _in_range(self, note, from_pitch, pitch_span, from_time, time_span):
        return (
            from_pitch <= note.pitch < from_pitch + pitch_span
            and from_time <= note.start_time < from_time + time_span
        )

    def get_notes_extended(self, from_pitch, pitch_span, from_time, time_span):
        return FakeVector(
            n for n in self._notes
            if self._in_range(n, from_pitch, pitch_span, from_time, time_span)
        )

    def add_new_notes(self, specs):
        for spec in specs:
            note = FakeMidiNote(
                self._next_note_id,
                spec.pitch,
                spec.start_time,
                spec.duration,
                velocity=spec.velocity,
                mute=spec.mute,
            )
            self._next_note_id += 1
            self._notes.append(note)

    def apply_note_modifications(self, notes):
        self.modifications_applied += 1

    def remove_notes_by_id(self, note_ids):
        self._notes = [n for n in self._notes if n.note_id not in note_ids]

    def remove_notes_extended(self, from_pitch, pitch_span, from_time, time_span):
        self._notes = [
            n for n in self._notes
            if not self._in_range(n, from_pitch, pitch_span, from_time, time_span)
        ]


class FakeMidiNoteSpecification:
    def __init__(self, pitch, start_time, duration, velocity=100.0, mute=False,
                 probability=1.0, velocity_deviation=0.0, release_velocity=64.0):
        self.pitch = pitch
        self.start_time = start_time
        self.duration = duration
        self.velocity = velocity
        self.mute = mute
        self.probability = probability
        self.velocity_deviation = velocity_deviation
        self.release_velocity = release_velocity


def install_fake_live_module():
    """Register a fake top-level Live module so handlers can import it."""
    import sys
    import types

    live = types.ModuleType("Live")
    live.Clip = types.SimpleNamespace(MidiNoteSpecification=FakeMidiNoteSpecification)
    sys.modules["Live"] = live


class FakeClipSlot:
    def __init__(self, clip=None):
        self.clip = clip
        self.fired = 0
        self.stopped = 0

    @property
    def has_clip(self):
        return self.clip is not None

    def fire(self):
        self.fired += 1

    def stop(self):
        self.stopped += 1

    def create_clip(self, length):
        self.clip = FakeClip(name="", length=length)

    def delete_clip(self):
        self.clip = None


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
        self.arrangement_clips = FakeVector(())
        self.mixer_device = FakeMixerDevice()
        self.stopped = 0

    def delete_device(self, index):
        devices = list(self.devices)
        devices.pop(index)
        self.devices = FakeVector(devices)

    def stop_all_clips(self):
        self.stopped += 1

    def duplicate_clip_to_arrangement(self, clip, time):
        copy = FakeClip(name=clip.name, length=clip.length,
                        is_midi=clip.is_midi_clip)
        copy.start_time = time
        copy.end_time = time + clip.length
        self.arrangement_clips = FakeVector(tuple(self.arrangement_clips) + (copy,))

    def delete_clip(self, clip):
        self.arrangement_clips = FakeVector(
            c for c in self.arrangement_clips if c is not clip
        )


class FakeMasterTrack:
    def __init__(self):
        self.name = "Master"
        self.color = 0x808080
        self.can_be_armed = False
        self.mute = False
        self.solo = False
        self.devices = FakeVector(())
        self.mixer_device = FakeMixerDevice(num_sends=0, is_master=True)


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
                            FakeDeviceParameter(
                                "Mode", 0.0, 0.0, 2.0, is_quantized=True,
                                value_items=("Low", "Mid", "High"),
                            ),
                        ),
                    ),
                ),
            ),
            FakeTrack(
                "Bass",
                devices=(
                    FakeRackDevice(
                        "Bass Rack",
                        chains=(
                            FakeChain(
                                "Chain 1",
                                devices=(
                                    FakeDevice(
                                        "Operator",
                                        parameters=(
                                            FakeDeviceParameter("Device On", 1.0),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                        parameters=(FakeDeviceParameter("Macro 1", 0.0),),
                    ),
                ),
            ),
        ),
        scenes=(FakeScene("Intro"), FakeScene("Drop", tempo=140.0)),
        return_tracks=(FakeTrack("A Reverb"),),
        cue_points=(FakeCuePoint("Verse", 0.0), FakeCuePoint("Chorus", 16.0)),
    )
