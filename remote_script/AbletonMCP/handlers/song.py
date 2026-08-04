"""Compound song-level reads and batched writes."""

from ..core.registry import CommandError
from . import common

SETTABLE = frozenset(
    [
        "tempo",
        "signature_numerator",
        "signature_denominator",
        "metronome",
        "loop",
        "loop_start",
        "loop_length",
        "record_mode",
        "session_record",
        "arrangement_overdub",
        "back_to_arranger",
        "clip_trigger_quantization",
        "midi_recording_quantization",
        "groove_amount",
        "current_song_time",
    ]
)


def register(registry, roots):
    def song():
        return roots["song"]()

    def get_song_status(params):
        s = song()
        get = common.safe_get
        return {
            "tempo": get(s, "tempo"),
            "signature": "%s/%s"
            % (get(s, "signature_numerator"), get(s, "signature_denominator")),
            "is_playing": get(s, "is_playing"),
            "current_song_time": get(s, "current_song_time"),
            "song_length": get(s, "song_length"),
            "loop": {
                "on": get(s, "loop"),
                "start": get(s, "loop_start"),
                "length": get(s, "loop_length"),
            },
            "metronome": get(s, "metronome"),
            "record_mode": get(s, "record_mode"),
            "session_record": get(s, "session_record"),
            "can_undo": get(s, "can_undo"),
            "can_redo": get(s, "can_redo"),
            "clip_trigger_quantization": get(s, "clip_trigger_quantization"),
            "midi_recording_quantization": get(s, "midi_recording_quantization"),
            "groove_amount": get(s, "groove_amount"),
            "root_note": get(s, "root_note"),
            "scale_name": get(s, "scale_name"),
            "num_tracks": len(get(s, "tracks", ())),
            "num_scenes": len(get(s, "scenes", ())),
            "num_returns": len(get(s, "return_tracks", ())),
        }

    def set_song(params):
        s = song()
        unknown = sorted(set(params) - SETTABLE)
        if unknown:
            raise CommandError(
                "cannot set %s; settable: %s"
                % (", ".join(unknown), ", ".join(sorted(SETTABLE)))
            )
        for name, value in params.items():
            common.set_with_float_retry(s, name, value)
        return get_song_status({})

    def get_tracks(params):
        s = song()
        tracks = [
            common.track_summary(track, i) for i, track in enumerate(s.tracks)
        ]
        returns = [
            common.track_summary(track, i, "return")
            for i, track in enumerate(s.return_tracks)
        ]
        master = common.track_summary(s.master_track, 0, "master")
        return {"tracks": tracks, "returns": returns, "master": master}

    def get_scenes(params):
        s = song()
        return {
            "scenes": [
                common.scene_summary(scene, i) for i, scene in enumerate(s.scenes)
            ]
        }

    def get_cue_points(params):
        s = song()
        cues = [
            {"index": i, "name": common.safe_get(c, "name"),
             "time": common.safe_get(c, "time")}
            for i, c in enumerate(common.safe_get(s, "cue_points", ()))
        ]
        return {"cue_points": sorted(cues, key=lambda c: c["time"] or 0)}

    registry.register_all(
        {
            "get_song_status": get_song_status,
            "set_song": set_song,
            "get_tracks": get_tracks,
            "get_scenes": get_scenes,
            "get_cue_points": get_cue_points,
        }
    )
