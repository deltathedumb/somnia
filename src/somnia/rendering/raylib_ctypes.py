"""CPython reference bindings for Somnia's flat raylib bridge."""

from __future__ import annotations

import ctypes
import os
from pathlib import Path


class CtypesRaylibBridge:
    """Load the Somnia raylib bridge through CPython's standard ctypes."""

    def __init__(self, path):
        self.path = Path(path).resolve()
        if not self.path.exists():
            raise FileNotFoundError("Somnia raylib bridge not found: " + str(self.path))
        if os.name == "nt" and hasattr(os, "add_dll_directory"):
            with os.add_dll_directory(str(self.path.parent)):
                self.library = ctypes.CDLL(str(self.path))
        else:
            self.library = ctypes.CDLL(str(self.path))
        self._configure()

    def _bind(self, name, arguments, result):
        function = getattr(self.library, name)
        function.argtypes = list(arguments)
        function.restype = result
        return function

    def _configure(self):
        integer = ctypes.c_int
        floating = ctypes.c_float
        string = ctypes.c_char_p

        self._open = self._bind(
            "somnia_raylib_open",
            [integer, integer, string],
            integer,
        )
        self._set_target_fps = self._bind(
            "somnia_raylib_set_target_fps",
            [integer],
            None,
        )
        self._should_close = self._bind(
            "somnia_raylib_should_close",
            [],
            integer,
        )
        self._frame_time = self._bind(
            "somnia_raylib_frame_time",
            [],
            floating,
        )
        self._begin_frame = self._bind(
            "somnia_raylib_begin_frame",
            [integer, integer, integer, integer],
            None,
        )
        self._begin_3d = self._bind(
            "somnia_raylib_begin_3d",
            [
                floating, floating, floating,
                floating, floating, floating,
                floating, floating, floating,
                floating, integer,
            ],
            None,
        )
        self._end_3d = self._bind("somnia_raylib_end_3d", [], None)
        self._end_frame = self._bind("somnia_raylib_end_frame", [], None)
        self._draw_grid = self._bind(
            "somnia_raylib_draw_grid",
            [integer, floating],
            None,
        )
        cube_arguments = [
            floating, floating, floating,
            floating, floating, floating,
            integer, integer, integer, integer,
        ]
        self._draw_cube = self._bind(
            "somnia_raylib_draw_cube",
            cube_arguments,
            None,
        )
        self._draw_cube_wires = self._bind(
            "somnia_raylib_draw_cube_wires",
            cube_arguments,
            None,
        )
        self._close = self._bind("somnia_raylib_close", [], None)

    def open(self, width, height, title):
        return int(self._open(int(width), int(height), str(title).encode("utf-8")))

    def set_target_fps(self, fps):
        self._set_target_fps(int(fps))

    def should_close(self):
        return bool(self._should_close())

    def frame_time(self):
        return float(self._frame_time())

    def begin_frame(self, red, green, blue, alpha):
        self._begin_frame(int(red), int(green), int(blue), int(alpha))

    def begin_3d(self, *values):
        self._begin_3d(*values)

    def end_3d(self):
        self._end_3d()

    def end_frame(self):
        self._end_frame()

    def draw_grid(self, slices, spacing):
        self._draw_grid(int(slices), float(spacing))

    def draw_cube(self, *values):
        self._draw_cube(*values)

    def draw_cube_wires(self, *values):
        self._draw_cube_wires(*values)

    def close(self):
        self._close()
