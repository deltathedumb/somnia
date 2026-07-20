"""Backend-neutral renderer contract."""

from __future__ import annotations

from somnia.model.scene import Camera, MeshObject, RenderService


class RenderFrame:
    """Deterministic render submission used for tests and backend handoff."""

    def __init__(self, camera_id="", camera=None, clear_color=None, commands=None):
        self.camera_id = camera_id
        self.camera = dict(camera or {})
        self.clear_color = clear_color
        self.commands = list(commands or [])

    def to_dict(self):
        return {
            "camera_id": self.camera_id,
            "camera": dict(self.camera),
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

    def should_close(self):
        return False

    def frame_time(self):
        return 0.0

    def clone_for_runtime(self):
        return type(self)()

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


def camera_state(camera):
    if camera is None:
        return {}
    return {
        "position": camera.transform.position.to_list(),
        "target": camera.target.to_list(),
        "up": camera.up.to_list(),
        "field_of_view": camera.field_of_view,
        "near_clip": camera.near_clip,
        "far_clip": camera.far_clip,
        "projection": camera.projection,
    }


def mesh_command(obj):
    return {
        "kind": "mesh",
        "object_id": obj.object_id,
        "name": obj.name,
        "mesh": obj.mesh,
        "material": obj.material,
        "color": obj.color.to_list(),
        "opacity": obj.opacity,
        "wireframe": obj.wireframe,
        "transform": obj.transform.to_dict(),
        "cast_shadows": obj.cast_shadows,
        "receive_shadows": obj.receive_shadows,
    }


def build_render_frame(data_model):
    """Build the canonical frame consumed by null and native renderers."""
    camera = find_active_camera(data_model)
    render_service = data_model.get_service(RenderService)
    clear_color = render_service.clear_color if render_service is not None else None
    commands = []
    for obj in collect_mesh_objects(data_model):
        commands.append(mesh_command(obj))
    return RenderFrame(
        camera_id=camera.object_id if camera is not None else "",
        camera=camera_state(camera),
        clear_color=clear_color,
        commands=commands,
    )
