"""A no-GPU renderer used for tests and compiler parity."""

from __future__ import annotations

from .base import Renderer, build_render_frame


class NullRenderer(Renderer):
    backend_name = "null"

    def __init__(self):
        self.initialized = False
        self.presented_frames = []

    def initialize(self, data_model):
        self.initialized = True
        return self

    def build_frame(self, data_model):
        if not self.initialized:
            raise RuntimeError("renderer is not initialized")
        return build_render_frame(data_model)

    def present(self, frame):
        if not self.initialized:
            raise RuntimeError("renderer is not initialized")
        self.presented_frames.append(frame)
        return frame

    def shutdown(self):
        self.initialized = False
