"""Generate a statically typed asmpython adapter for the raylib bridge."""

from __future__ import annotations

from .raylib import create_raylib_library


def generate_raylib_bridge_source(platform=None):
    library = create_raylib_library()
    binding_source = library.generated_binding_source(
        variable_name="_raylib_library",
        platform=platform,
    )
    adapter = '''

class GeneratedRaylibBridge:
    def open(self, width: int, height: int, title: str) -> int:
        return somnia_raylib_open(width, height, title)

    def set_target_fps(self, fps: int) -> None:
        somnia_raylib_set_target_fps(fps)

    def should_close(self) -> int:
        return somnia_raylib_should_close()

    def frame_time(self) -> float:
        return somnia_raylib_frame_time()

    def begin_frame(self, red: int, green: int, blue: int, alpha: int) -> None:
        somnia_raylib_begin_frame(red, green, blue, alpha)

    def begin_3d(
        self,
        position_x: float,
        position_y: float,
        position_z: float,
        target_x: float,
        target_y: float,
        target_z: float,
        up_x: float,
        up_y: float,
        up_z: float,
        field_of_view: float,
        projection: int,
    ) -> None:
        somnia_raylib_begin_3d(
            position_x,
            position_y,
            position_z,
            target_x,
            target_y,
            target_z,
            up_x,
            up_y,
            up_z,
            field_of_view,
            projection,
        )

    def end_3d(self) -> None:
        somnia_raylib_end_3d()

    def end_frame(self) -> None:
        somnia_raylib_end_frame()

    def draw_grid(self, slices: int, spacing: float) -> None:
        somnia_raylib_draw_grid(slices, spacing)

    def draw_cube(
        self,
        position_x: float,
        position_y: float,
        position_z: float,
        size_x: float,
        size_y: float,
        size_z: float,
        red: int,
        green: int,
        blue: int,
        alpha: int,
    ) -> None:
        somnia_raylib_draw_cube(
            position_x,
            position_y,
            position_z,
            size_x,
            size_y,
            size_z,
            red,
            green,
            blue,
            alpha,
        )

    def draw_cube_wires(
        self,
        position_x: float,
        position_y: float,
        position_z: float,
        size_x: float,
        size_y: float,
        size_z: float,
        red: int,
        green: int,
        blue: int,
        alpha: int,
    ) -> None:
        somnia_raylib_draw_cube_wires(
            position_x,
            position_y,
            position_z,
            size_x,
            size_y,
            size_z,
            red,
            green,
            blue,
            alpha,
        )

    def close(self) -> None:
        somnia_raylib_close()


bridge = GeneratedRaylibBridge()
'''
    return binding_source.rstrip() + adapter
