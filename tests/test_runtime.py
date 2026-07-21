from __future__ import annotations

import unittest

from somnia import (
    Camera,
    Engine,
    MeshObject,
    NativeFunction,
    NativeLibrary,
    PortaPyRuntime,
    PythonScript,
    ServerScriptProvider,
    World,
)
from somnia.math import Transform, Vec3
from somnia.scripting import CPythonReferenceBackend, ScriptHost


class RuntimeFoundationTests(unittest.TestCase):
    def test_null_renderer_reads_the_live_object_hierarchy(self) -> None:
        engine = Engine()
        world = engine.data_model.get_service(World)

        camera = Camera(object_id="camera", name="MainCamera")
        world.add_child(camera)

        cube = MeshObject(object_id="cube", name="Cube")
        cube.mesh = "builtin:cube"
        cube.material = "materials/purple.sem"
        cube.transform = Transform(position=Vec3(1.0, 2.0, 3.0))
        world.add_child(cube)

        frame = engine.frame().to_dict()
        self.assertEqual(frame["camera_id"], "camera")
        self.assertEqual(len(frame["commands"]), 1)
        self.assertEqual(frame["commands"][0]["object_id"], "cube")
        self.assertEqual(
            frame["commands"][0]["transform"]["position"],
            [1.0, 2.0, 3.0],
        )

    def test_native_library_generates_static_asmpython_bindings(self) -> None:
        library = NativeLibrary(name="Core")
        library.windows_path = "core.dll"
        function = NativeFunction(name="add_values")
        function.arguments = ["int", "int"]
        function.result = "int"
        library.add_child(function)

        source = library.generated_binding_source(platform="win32")
        self.assertIn("library = import_binary(", source)
        self.assertIn("core.dll", source)
        self.assertIn("@library.imported", source)
        self.assertIn("def add_values(arg0: int, arg1: int) -> int:", source)

    def test_reference_script_backend_uses_portapy_runtime_objects(self) -> None:
        runtime = PortaPyRuntime(object_id="portapy", name="PortaPy")
        script = PythonScript(object_id="startup", name="Startup")
        script.source = 'somnia["counter"] = somnia["counter"] + 1'
        runtime.add_child(script)

        host_api = {"counter": 41}
        host = ScriptHost(runtime, CPythonReferenceBackend(), host_api)
        results = host.run_auto_scripts()

        self.assertEqual(len(results), 1)
        self.assertEqual(host_api["counter"], 42)
        self.assertTrue(runtime.runtime_created)
        host.stop()
        self.assertFalse(runtime.runtime_created)

    def test_scripts_access_providers_through_game_realm_roots(self) -> None:
        engine = Engine()
        server_scripts = engine.get_provider(ServerScriptProvider)
        runtime = PortaPyRuntime(object_id="portapy-script-api", name="PortaPy")
        script = PythonScript(object_id="hierarchy-script", name="Hierarchy")
        script.execution_context = "server"
        script.source = (
            "server = game.server\n"
            "physics_provider = server.PhysicsProvider\n"
            'somnia["physics_id"] = physics_provider.object_id\n'
        )
        runtime.add_child(script)
        server_scripts.add_child(runtime)

        host_api = {}
        host = ScriptHost(runtime, CPythonReferenceBackend(), host_api)
        engine.attach_script_host(host)
        results = engine.start_scripts(context="server")

        self.assertEqual(len(results), 1)
        self.assertEqual(host_api["physics_id"], "provider:server:PhysicsProvider")
        self.assertIs(host.resolve_game(), engine.data_model)
        engine.shutdown()


if __name__ == "__main__":
    unittest.main()
