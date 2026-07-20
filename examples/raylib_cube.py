"""Open Somnia's first raylib window and render a cube on a grid."""

from somnia import Camera, Engine, MeshObject, RaylibRenderer, World
from somnia.math import Transform, Vec3


def main():
    renderer = RaylibRenderer(
        width=1280,
        height=720,
        title="Somnia Engine - First Light",
        target_fps=60,
    )
    engine = Engine(renderer=renderer)
    world = engine.data_model.get_service(World)

    camera = Camera(name="MainCamera")
    camera.transform = Transform(position=Vec3(6.0, 5.0, 6.0))
    camera.target = Vec3(0.0, 1.0, 0.0)
    world.add_child(camera)

    cube = MeshObject(name="Pixelated Purple Cube")
    cube.mesh = "builtin:cube"
    cube.transform = Transform(
        position=Vec3(0.0, 1.0, 0.0),
        scale=Vec3(2.0, 2.0, 2.0),
    )
    world.add_child(cube)

    try:
        engine.run()
    finally:
        engine.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
