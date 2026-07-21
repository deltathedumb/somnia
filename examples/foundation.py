"""Demonstrate Somnia's realm-root editor/runtime foundation."""

from somnia import (
    ExportType,
    MeshObject,
    ModelDocument,
    NativeFunction,
    NativeLibrary,
    PortaPyRuntime,
    Property,
    PythonScript,
    register_object_class,
)
from somnia.editor import EditorSession
from somnia.formats import dumps_sem, dumps_semj
from somnia.math import Transform, Vec3
from somnia.runtime import Engine


@register_object_class("example.Spinner")
class Spinner(MeshObject):
    speed = Property(1.0, value_type=float, category="Spinner", minimum=0.0)


def main():
    engine = Engine()
    editor = EditorSession(engine)
    game = engine.data_model
    scene = game.shared.Scene

    camera = editor.create_object("somnia.Camera", scene, name="MainCamera")
    camera.transform = Transform(position=Vec3(5.0, 4.0, 5.0))

    cube = editor.create_object("example.Spinner", scene, name="Cube")
    cube.mesh = "builtin:cube"
    cube.material = "builtin:pixelated-purple"
    editor.set_property(cube, "speed", 2.5)

    shared_assets = game.shared.Assets
    project_core = NativeLibrary(name="ProjectCore")
    project_core.load_on_start = False
    project_core.windows_path = "native/project_core.dll"
    project_core.linux_path = "native/libproject_core.so"
    add_values = NativeFunction(name="project_add")
    add_values.arguments = ["int", "int"]
    project_core.add_child(add_values)
    shared_assets.add_child(project_core)

    server_scripts = game.server.ServerScriptProvider
    portapy = PortaPyRuntime(name="PortaPy")
    portapy.load_on_start = False
    startup = PythonScript(name="Startup")
    startup.execution_context = "server"
    startup.source = (
        "server = game.server\n"
        "physics_provider = server.PhysicsProvider\n"
        'print("Somnia embedded server Python started", physics_provider)\n'
    )
    portapy.add_child(startup)
    server_scripts.add_child(portapy)

    frame = engine.frame()
    document = ModelDocument("Foundation", [game])
    client_manifest = engine.create_export_plan(ExportType.CLIENT).manifest()

    print("Top-level roots:", [root.name for root in game.realm_roots()])
    print("Objects:", len(list(game.walk(include_self=True))))
    print("Draw commands:", len(frame.commands))
    print("SEMJ bytes:", len(dumps_semj(document).encode("utf-8")))
    print("SEM bytes:", len(dumps_sem(document)))
    print("Client export packages:", [item["realm"] for item in client_manifest["packages"]])
    print("Generated native binding:")
    print(project_core.generated_binding_source())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
