"""Backend-neutral renderer contract."""

from __future__ import annotations

from somnia.model.scene import Camera, MeshObject, RenderService


class RenderFrame:
    """Deterministic render submission used for tests and backend handoff."""

    def __init__(self, camera_id="", clear_color=None, commands=None):
        self.camera_id = camera_id
        self.clear_color = clear_color
        self.commands = list(commands or [])

    def to_dict(self):
        return {
            "camera_id": self.camera_id,
            "clear_color": (
                self.clear_color.to_list() if self.clear_color is not None else None
            ),
            "commands": list(self.commands),
        }


class Renderer:
    """Interface implemented by raylib and future rendering backends."""

    backend_name = "base"

    def initialize(self, data_model):
        raise NotImplementedError

    def build_frame(self, data_model):
        raise NotImplementedError

    def present(self, frame):
        raise NotImplementedError

    def shutdown(self):
        raise NotImplementedError


def find_active_camera(data_model):
    render_service = data_model.get_service(RenderService)
    requested_id = render_service.active_camera_id if render_service is not None else ""
    first_active = None
    for obj in data_model.walk(include_self=True):
        if isinstance(obj, Camera) and obj.enabled and obj.active:
            if first_active is None:
                first_active = obj
            if requested_id and obj.object_id == requested_id:
                return obj
    return first_active


def collect_mesh_objects(data_model):
    return [
        obj
        for obj in data_model.walk(include_self=True)
        if isinstance(obj, MeshObject) and obj.enabled and obj.visible
    ]
