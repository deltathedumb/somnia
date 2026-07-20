"""Deterministic observable snapshot for CPython/asmpython comparison."""

import json

from somnia import Camera, Game, MeshObject, Scene
from somnia.math import Transform, Vec3
from somnia.runtime import Engine


def main():
    data_model = Game(object_id="data", name="Parity")
    engine = Engine(data_model=data_model)
    scene = engine.get_provider(Scene)

    camera = Camera(object_id="camera", name="Camera")
    scene.add_child(camera)

    cube = MeshObject(object_id="cube", name="Cube")
    cube.mesh = "builtin:cube"
    cube.transform = Transform(position=Vec3(3.0, 4.0, 5.0))
    scene.add_child(cube)

    frame = engine.frame().to_dict()
    snapshot = {
        "frame": frame,
        "providers": [provider.provider_key for provider in data_model.providers()],
        "objects": [
            {
                "id": obj.object_id,
                "name": obj.name,
                "parent": obj.parent.object_id if obj.parent is not None else None,
                "type": obj.type_name,
            }
            for obj in data_model.walk(include_self=True)
            if not obj.type_name.startswith("somnia.editor.")
        ],
    }
    print(json.dumps(snapshot, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
