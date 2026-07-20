"""Somnia rendering backend interfaces."""

from .base import (
    RenderFrame,
    Renderer,
    build_render_frame,
    collect_mesh_objects,
    find_active_camera,
)
from .null import NullRenderer
from .raylib import (
    RAYLIB_BRIDGE_NAME,
    RaylibRenderer,
    RecordingRaylibBridge,
    create_raylib_library,
    ensure_raylib_library,
)

__all__ = [
    "NullRenderer",
    "RAYLIB_BRIDGE_NAME",
    "RaylibRenderer",
    "RecordingRaylibBridge",
    "RenderFrame",
    "Renderer",
    "build_render_frame",
    "collect_mesh_objects",
    "create_raylib_library",
    "ensure_raylib_library",
    "find_active_camera",
]
