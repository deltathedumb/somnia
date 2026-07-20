"""Raylib renderer backed by Somnia's flat native bridge ABI."""

from __future__ import annotations

from somnia.model import NativeFunction, NativeLibrary, NativeLibraryService, RenderService

from .base import Renderer, build_render_frame


RAYLIB_BRIDGE_NAME = "SomniaRaylibBridge"


def _function(name, arguments, result="none"):
    function = NativeFunction(name=name)
    function.symbol = name
    function.arguments = list(arguments)
    function.result = result
    return function


def create_raylib_library():
    """Create the serializable DLL/SO declaration for Somnia's raylib bridge."""
    library = NativeLibrary(name=RAYLIB_BRIDGE_NAME)
    library.windows_path = "native/somnia_raylib_bridge.dll"
    library.linux_path = "native/libsomnia_raylib_bridge.so"
    library.macos_path = "native/libsomnia_raylib_bridge.dylib"
    library.load_on_start = False
    library.required = True
    library.expose_to_scripts = False

    declarations = [
        ("somnia_raylib_open", ["int", "int", "str"], "int"),
        ("somnia_raylib_set_target_fps", ["int"], "none"),
        ("somnia_raylib_should_close", [], "int"),
        ("somnia_raylib_frame_time", [], "float"),
        ("somnia_raylib_begin_frame", ["int", "int", "int", "int"], "none"),
        (
            "somnia_raylib_begin_3d",
            [
                "float", "float", "float",
                "float", "float", "float",
                "float", "float", "float",
                "float", "int",
            ],
            "none",
        ),
        ("somnia_raylib_end_3d", [], "none"),
        ("somnia_raylib_end_frame", [], "none"),
        ("somnia_raylib_draw_grid", ["int", "float"], "none"),
        (
            "somnia_raylib_draw_cube",
            [
                "float", "float", "float",
                "float", "float", "float",
                "int", "int", "int", "int",
            ],
            "none",
        ),
        (
            "somnia_raylib_draw_cube_wires",
            [
                "float", "float", "float",
                "float", "float", "float",
                "int", "int", "int", "int",
            ],
            "none",
        ),
        ("somnia_raylib_close", [], "none"),
    ]
    for name, arguments, result in declarations:
        library.add_child(_function(name, arguments, result))
    return library


def ensure_raylib_library(data_model):
    service = data_model.ensure_service(NativeLibraryService)
    for library in service.libraries():
        if library.name == RAYLIB_BRIDGE_NAME:
            return library
    library = create_raylib_library()
    service.add_child(library)
    return library


def _channel(value):
    numeric = float(value)
    if numeric < 0.0:
        numeric = 0.0
    if numeric > 1.0:
        numeric = 1.0
    return int(round(numeric * 255.0))


def _rgba(color, opacity=1.0):
    values = color.to_list() if hasattr(color, "to_list") else list(color)
    return (
        _channel(values[0]),
        _channel(values[1]),
        _channel(values[2]),
        _channel(opacity),
    )


class RecordingRaylibBridge:
    """In-memory raylib bridge used by tests and editor diagnostics."""

    def __init__(self, open_result=1, close_after_frames=None):
        self.open_result = int(open_result)
        self.close_after_frames = close_after_frames
        self.frames = 0
        self.calls = []

    def open(self, width, height, title):
        self.calls.append(("open", width, height, title))
        return self.open_result

    def set_target_fps(self, fps):
        self.calls.append(("set_target_fps", fps))

    def should_close(self):
        self.calls.append(("should_close",))
        if self.close_after_frames is None:
            return False
        return self.frames >= self.close_after_frames

    def frame_time(self):
        self.calls.append(("frame_time",))
        return 1.0 / 60.0

    def begin_frame(self, red, green, blue, alpha):
        self.calls.append(("begin_frame", red, green, blue, alpha))

    def begin_3d(self, *values):
        self.calls.append(("begin_3d",) + tuple(values))

    def end_3d(self):
        self.calls.append(("end_3d",))

    def end_frame(self):
        self.calls.append(("end_frame",))
        self.frames += 1

    def draw_grid(self, slices, spacing):
        self.calls.append(("draw_grid", slices, spacing))

    def draw_cube(self, *values):
        self.calls.append(("draw_cube",) + tuple(values))

    def draw_cube_wires(self, *values):
        self.calls.append(("draw_cube_wires",) + tuple(values))

    def close(self):
        self.calls.append(("close",))


class RaylibRenderer(Renderer):
    """First visual backend consuming the canonical Somnia RenderFrame."""

    backend_name = "raylib"

    def __init__(
        self,
        bridge=None,
        width=1280,
        height=720,
        title="Somnia Engine",
        target_fps=60,
        draw_grid=True,
        grid_slices=20,
        grid_spacing=1.0,
    ):
        self.bridge = bridge
        self.width = int(width)
        self.height = int(height)
        self.title = str(title)
        self.target_fps = int(target_fps)
        self.draw_grid_enabled = bool(draw_grid)
        self.grid_slices = int(grid_slices)
        self.grid_spacing = float(grid_spacing)
        self.initialized = False
        self.library = None
        self.unsupported_meshes = []

    def initialize(self, data_model):
        if self.initialized:
            return self
        self.library = ensure_raylib_library(data_model)
        if self.bridge is None:
            from .raylib_ctypes import CtypesRaylibBridge

            self.bridge = CtypesRaylibBridge(self.library.selected_path())
        if not self.bridge.open(self.width, self.height, self.title):
            raise RuntimeError("raylib bridge could not open the Somnia window")
        self.bridge.set_target_fps(self.target_fps)
        render_service = data_model.get_service(RenderService)
        if render_service is not None:
            render_service.backend = self.backend_name
        self.initialized = True
        return self

    def build_frame(self, data_model):
        if not self.initialized:
            raise RuntimeError("renderer is not initialized")
        return build_render_frame(data_model)

    def present(self, frame):
        if not self.initialized:
            raise RuntimeError("renderer is not initialized")

        clear = _rgba(frame.clear_color or (0.0, 0.0, 0.0), 1.0)
        self.bridge.begin_frame(*clear)
        camera = frame.camera
        if camera:
            position = camera["position"]
            target = camera["target"]
            up = camera["up"]
            projection = 1 if camera["projection"] == "orthographic" else 0
            self.bridge.begin_3d(
                position[0], position[1], position[2],
                target[0], target[1], target[2],
                up[0], up[1], up[2],
                camera["field_of_view"], projection,
            )
            if self.draw_grid_enabled:
                self.bridge.draw_grid(self.grid_slices, self.grid_spacing)
            for command in frame.commands:
                self._draw_command(command)
            self.bridge.end_3d()
        self.bridge.end_frame()
        return frame

    def _draw_command(self, command):
        if command.get("kind") != "mesh":
            return
        mesh = command.get("mesh") or "builtin:cube"
        if mesh != "builtin:cube":
            self.unsupported_meshes.append((command.get("object_id", ""), mesh))
            return
        transform = command["transform"]
        position = transform["position"]
        scale = transform["scale"]
        color = command.get("color", [1.0, 1.0, 1.0])
        opacity = command.get("opacity", 1.0)
        rgba = _rgba(color, opacity)
        arguments = (
            position[0], position[1], position[2],
            scale[0], scale[1], scale[2],
            rgba[0], rgba[1], rgba[2], rgba[3],
        )
        if command.get("wireframe", False):
            self.bridge.draw_cube_wires(*arguments)
        else:
            self.bridge.draw_cube(*arguments)

    def should_close(self):
        if not self.initialized:
            return False
        return bool(self.bridge.should_close())

    def frame_time(self):
        if not self.initialized:
            return 0.0
        return float(self.bridge.frame_time())

    def shutdown(self):
        if self.initialized:
            self.bridge.close()
        self.initialized = False
