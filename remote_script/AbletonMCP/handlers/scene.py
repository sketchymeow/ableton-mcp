"""Scene CRUD and firing."""

from ..core.registry import CommandError
from . import common

SETTABLE = frozenset(["name", "color", "tempo"])


def register(registry, roots):
    def song():
        return roots["song"]()

    def create_scene(params):
        s = song()
        index = params.get("index", -1)
        s.create_scene(index)
        new_index = index if index >= 0 else len(s.scenes) - 1
        return common.scene_summary(s.scenes[new_index], new_index)

    def delete_scene(params):
        s = song()
        index = common.require(params, "index")
        common.get_scene(s, index)
        s.delete_scene(index)
        return {"deleted": index}

    def duplicate_scene(params):
        s = song()
        index = common.require(params, "index")
        common.get_scene(s, index)
        s.duplicate_scene(index)
        return common.scene_summary(s.scenes[index + 1], index + 1)

    def fire_scene(params):
        s = song()
        index = common.require(params, "index")
        common.get_scene(s, index).fire()
        return {"fired": index}

    def set_scene(params):
        s = song()
        index = common.require(params, "index")
        scene = common.get_scene(s, index)
        props = dict(params)
        props.pop("index", None)
        unknown = sorted(set(props) - SETTABLE)
        if unknown:
            raise CommandError(
                "cannot set %s; settable: %s"
                % (", ".join(unknown), ", ".join(sorted(SETTABLE)))
            )
        for name, value in props.items():
            if name == "color":
                value = common.parse_color(value)
            common.set_with_float_retry(scene, name, value)
        return common.scene_summary(scene, index)

    registry.register_all(
        {
            "create_scene": create_scene,
            "delete_scene": delete_scene,
            "duplicate_scene": duplicate_scene,
            "fire_scene": fire_scene,
            "set_scene": set_scene,
        }
    )
