"""Demonstrate Somnia's first unified editor/runtime slice."""

from somnia import (
    Camera,
    MeshObject,
    ModelDocument,
    NativeFunction,
    NativeLibrary,
    NativeLibraryService,
    PortaPyRuntime,
    Property,
    PythonScript,
    ScriptService,
    World,
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
    world = engine.data_model.get_service(World)

    camera = editor.create_object("somnia.Camera", world, name="MainCamera")
    camera.transform = Transform(position=Vec3(5.0, 4.0, 5.0))

    cube = editor.create_object("example.Spinner", world, name="Cube")
    cube.mesh = "builtin:cube"
    cube.material = "builtin:pixelated-purple"
    editor.set_property(cube, "speed", 2.5)

    native_service = engine.data_model.get_service(NativeLibraryService)
    project_core = NativeLibrary(name="ProjectCore")
    project_core.load_on_start = False
    project_core.windows_path = "native/project_core.dll"
    project_core.linux_path = "native/libproject_core.so"
    add_values = NativeFunction(name="project_add")
    add_values.arguments = ["int", "int"]
    project_core.add_child(add_values)
    native_service.add_child(project_core)

    script_service = engine.data_model.get_service(ScriptService)
    portapy = PortaPyRuntime(name="PortaPy")
    startup = PythonScript(name="Startup")
    startup.source = 'print("Somnia embedded Python started")'
    portapy.add_child(startup)
    script_service.add_child(portapy)

    frame = engine.frame()
    document = ModelDocument("Foundation", [engine.data_model])

    print("Objects:", len(list(engine.data_model.walk(include_self=True))))
    print("Draw commands:", len(frame.commands))
    print("SEMJ bytes:", len(dumps_semj(document).encode("utf-8")))
    print("SEM bytes:", len(dumps_sem(document)))
    print("Generated native binding:")
    print(project_core.generated_binding_source())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
