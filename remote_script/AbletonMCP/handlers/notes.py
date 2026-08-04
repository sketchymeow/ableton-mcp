"""MIDI note read/write/modify using the Live 11+ note APIs.

Notes carry stable IDs (from get_notes_extended), so edits are surgical:
read what's there, modify by ID, add or remove selectively. No blind
whole-clip overwrites.
"""

from ..core.registry import CommandError
from . import common

FULL_RANGE = (0, 128, -16384.0, 32768.0)

NOTE_FIELDS = ("pitch", "start_time", "duration", "velocity", "mute")
EXTRA_FIELDS = ("probability", "velocity_deviation", "release_velocity")


def _note_dict(note):
    data = {
        "note_id": common.safe_get(note, "note_id"),
        "pitch": note.pitch,
        "start_time": note.start_time,
        "duration": note.duration,
        "velocity": note.velocity,
        "mute": note.mute,
    }
    for field in EXTRA_FIELDS:
        value = common.safe_get(note, field)
        if value is not None:
            data[field] = value
    return data


def _range_args(params):
    return (
        int(params.get("from_pitch", FULL_RANGE[0])),
        int(params.get("pitch_span", FULL_RANGE[1])),
        float(params.get("from_time", FULL_RANGE[2])),
        float(params.get("time_span", FULL_RANGE[3])),
    )


def _midi_clip(song, params):
    clip = common.get_clip(song, params)
    if not common.safe_get(clip, "is_midi_clip"):
        raise CommandError("not a MIDI clip")
    return clip


def register(registry, roots):
    def song():
        return roots["song"]()

    def get_notes(params):
        clip = _midi_clip(song(), params)
        notes = clip.get_notes_extended(*_range_args(params))
        return {"notes": [_note_dict(n) for n in notes]}

    def add_notes(params):
        clip = _midi_clip(song(), params)
        specs = params.get("notes")
        if not isinstance(specs, list) or not specs:
            raise CommandError("notes must be a non-empty list")
        import Live

        new_notes = []
        for i, spec in enumerate(specs):
            if not isinstance(spec, dict):
                raise CommandError("note %d must be an object" % i)
            missing = [f for f in ("pitch", "start_time", "duration") if f not in spec]
            if missing:
                raise CommandError("note %d missing: %s" % (i, ", ".join(missing)))
            kwargs = {
                "pitch": int(spec["pitch"]),
                "start_time": float(spec["start_time"]),
                "duration": float(spec["duration"]),
                "velocity": float(spec.get("velocity", 100)),
                "mute": bool(spec.get("mute", False)),
            }
            for field in EXTRA_FIELDS:
                if field in spec:
                    kwargs[field] = float(spec[field])
            new_notes.append(Live.Clip.MidiNoteSpecification(**kwargs))
        clip.add_new_notes(tuple(new_notes))
        notes = clip.get_notes_extended(*FULL_RANGE)
        return {"added": len(new_notes), "notes": [_note_dict(n) for n in notes]}

    def update_notes(params):
        clip = _midi_clip(song(), params)
        changes = params.get("notes")
        if not isinstance(changes, list) or not changes:
            raise CommandError("notes must be a non-empty list")
        current = clip.get_notes_extended(*FULL_RANGE)
        by_id = dict((common.safe_get(n, "note_id"), n) for n in current)
        touched = []
        for change in changes:
            if not isinstance(change, dict) or "note_id" not in change:
                raise CommandError("each update needs a note_id")
            note = by_id.get(change["note_id"])
            if note is None:
                raise CommandError("no note with id %s" % change["note_id"])
            for field in NOTE_FIELDS + EXTRA_FIELDS:
                if field in change:
                    setattr(note, field, change[field])
            touched.append(note)
        clip.apply_note_modifications(current)
        return {"updated": len(touched), "notes": [_note_dict(n) for n in touched]}

    def remove_notes(params):
        clip = _midi_clip(song(), params)
        note_ids = params.get("note_ids")
        if note_ids is not None:
            if not isinstance(note_ids, list) or not note_ids:
                raise CommandError("note_ids must be a non-empty list")
            clip.remove_notes_by_id(tuple(int(i) for i in note_ids))
            return {"removed": len(note_ids)}
        clip.remove_notes_extended(*_range_args(params))
        return {"removed": "range"}

    registry.register_all(
        {
            "get_notes": get_notes,
            "add_notes": add_notes,
            "update_notes": update_notes,
            "remove_notes": remove_notes,
        }
    )
