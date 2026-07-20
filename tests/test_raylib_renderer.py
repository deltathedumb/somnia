from __future__ import annotations

import unittest

from somnia import Camera, Engine, MeshObject, RaylibRenderer, RecordingRaylibBridge, World
from somnia.math import Transform, Vec3
from somnia.rendering import create_raylib_library
from somnia.rendering.raylib_codegen import generate_raylib_bridge_source


class RaylibRendererTests(unittest.TestCase):
    def make_engine(self, bridge):
        renderer = RaylibRenderer(
            bridge=bridge,
            width=800,
            height=450,
            title="Somnia Test",
            target_fps=60,
            grid_slices=12,
            grid_spacing=0.5,
        )
        engine = Engine(renderer=renderer)
        world = engine.data_model.get_service(World)

        camera = Camera(object_id="camera", name="Camera")
        camera.transform = Transform(position=Vec3(5.0, 4.0, 5.0))
        camera.target = Vec3.zero()
        world.add_child(camera)

        cube = MeshObject(object_id="cube", name="Cube")
        cube.mesh = "builtin:cube"
        cube.transform = Transform(
            position=Vec3(1.0, 2.0, 3.0),
            scale=Vec3(2.0, 3.0, 4.0),
        )
        world.add_child(cube)
        return engine

    def test_renderer_consumes_canonical_frame(self) -> None:
        bridge = RecordingRaylibBridge(close_after_frames=1)
        engine = self.make_engine(bridge)

        frames = engine.run()
        engine.shutdown()

        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].camera_id, "camera")
        names = [call[0] for call in bridge.calls]
        self.assertEqual(names[0:2], ["open", "set_target_fps"])
        self.assertIn("begin_frame", names)
        self.assertIn("begin_3d", names)
        self.assertIn("draw_grid", names)
        self.assertIn("draw_cube", names)
        self.assertIn("end_3d", names)
        self.assertIn("end_frame", names)
        self.assertEqual(names[-1], "close")

        draw_cube = next(call for call in bridge.calls if call[0] == "draw_cube")
        self.assertEqual(draw_cube[1:7], (1.0, 2.0, 3.0, 2.0, 3.0, 4.0))
        self.assertEqual(draw_cube[7:11], (149, 0, 255, 255))
        self.assertAlmostEqual(engine.delta_time, 1.0 / 60.0)

    def test_wireframe_and_unsupported_meshes(self) -> None:
        bridge = RecordingRaylibBridge(close_after_frames=1)
        engine = self.make_engine(bridge)
        world = engine.data_model.get_service(World)
        cube = world.find_first("Cube")
        cube.wireframe = True

        unsupported = MeshObject(object_id="mesh", name="ImportedMesh")
        unsupported.mesh = "models/example.mesh"
        world.add_child(unsupported)

        engine.run()

        names = [call[0] for call in bridge.calls]
        self.assertIn("draw_cube_wires", names)
        self.assertNotIn("draw_cube", names)
        self.assertEqual(
            engine.renderer.unsupported_meshes,
            [("mesh", "models/example.mesh")],
        )

    def test_native_library_manifest_generates_static_bindings(self) -> None:
        library = create_raylib_library()
        functions = library.functions()
        names = [function.export_name() for function in functions]

        self.assertIn("somnia_raylib_open", names)
        self.assertIn("somnia_raylib_begin_3d", names)
        self.assertIn("somnia_raylib_draw_cube", names)
        self.assertIn("somnia_raylib_close", names)

        source = library.generated_binding_source(platform="linux")
        self.assertIn("libsomnia_raylib_bridge.so", source)
        self.assertIn("@library.imported", source)
        self.assertIn("def somnia_raylib_open", source)
        self.assertIn("def somnia_raylib_draw_cube", source)

    def test_generated_adapter_is_valid_python(self) -> None:
        source = generate_raylib_bridge_source(platform="linux")
        compile(source, "<generated-raylib-bridge>", "exec")
        self.assertIn("class GeneratedRaylibBridge", source)
        self.assertIn("bridge = GeneratedRaylibBridge()", source)
        self.assertIn("def begin_3d(", source)
        self.assertIn("def draw_cube_wires(", source)


if __name__ == "__main__":
    unittest.main()
