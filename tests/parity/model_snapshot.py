"""Deterministic observable snapshot for CPython/asmpython comparison."""

import json

from somnia import Camera, DataModel, MeshObject, World
from somnia.math import Transform, Vec3
from somnia.runtime import Engine


def main():
    data_model = DataModel(object_id="data", name="Parity")
    engine = Engine(data_model=data_model)
    world = data_model.get_service(World)

    camera = Camera(object_id="camera", name="Camera")
    world.add_child(camera)

    cube = MeshObject(object_id="cube", name="Cube")
    cube.mesh = "builtin:cube"
    cube.transform = Transform(position=Vec3(3.0, 4.0, 5.0))
    world.add_child(cube)

    frame = engine.frame().to_dict()
    snapshot = {
        "frame": frame,
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
