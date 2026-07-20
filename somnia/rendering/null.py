"""A no-GPU renderer used for tests and compiler parity."""

from __future__ import annotations

from somnia.model.scene import RenderService

from .base import RenderFrame, Renderer, collect_mesh_objects, find_active_camera


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
        camera = find_active_camera(data_model)
        render_service = data_model.get_service(RenderService)
        clear_color = render_service.clear_color if render_service is not None else None
        commands = []
        for obj in collect_mesh_objects(data_model):
            commands.append(
                {
                    "kind": "mesh",
                    "object_id": obj.object_id,
                    "name": obj.name,
                    "mesh": obj.mesh,
                    "material": obj.material,
                    "transform": obj.transform.to_dict(),
                    "cast_shadows": obj.cast_shadows,
                    "receive_shadows": obj.receive_shadows,
                }
            )
        return RenderFrame(
            camera_id=camera.object_id if camera is not None else "",
            clear_color=clear_color,
            commands=commands,
        )

    def present(self, frame):
        if not self.initialized:
            raise RuntimeError("renderer is not initialized")
        self.presented_frames.append(frame)
        return frame

    def shutdown(self):
        self.initialized = False
