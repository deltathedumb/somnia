"""Scene objects and visible world providers shared by editor and runtime."""

from __future__ import annotations

from somnia.math import Vec3

from .core import ModelNode, Property, Service, register_object_class
from .provider import Provider, RealmKey, RuntimeRealm


@register_object_class("somnia.Scene")
class Scene(Provider):
    """Workspace-equivalent provider containing the live spatial hierarchy."""

    provider_key = "Scene"
    fixed_name = "Scene"
    runtime_realms = (RuntimeRealm.SERVER, RuntimeRealm.CLIENT)
    root_keys = (RealmKey.SHARED,)
    default_root_key = RealmKey.SHARED

    active_camera_id = Property("", value_type=str, category="Scene")


# Backward-compatible source alias. New serialized documents use somnia.Scene.
World = Scene


@register_object_class("somnia.Environment")
class Environment(Provider):
    """Lighting-equivalent provider for client visual environment state."""

    provider_key = "Environment"
    fixed_name = "Environment"
    runtime_realms = (RuntimeRealm.CLIENT,)
    root_keys = (RealmKey.CLIENT,)
    default_root_key = RealmKey.CLIENT

    clear_color = Property(Vec3(0.05, 0.05, 0.08), value_type=Vec3, category="Environment")
    ambient_color = Property(Vec3(0.2, 0.2, 0.2), value_type=Vec3, category="Environment")
    fog_color = Property(Vec3(0.5, 0.5, 0.5), value_type=Vec3, category="Environment")
    fog_start = Property(0.0, value_type=float, category="Environment", minimum=0.0)
    fog_end = Property(1000.0, value_type=float, category="Environment", minimum=0.0)
    time_of_day = Property(12.0, value_type=float, category="Environment", minimum=0.0, maximum=24.0)


@register_object_class("somnia.Camera")
class Camera(ModelNode):
    field_of_view = Property(
        70.0,
        value_type=float,
        category="Camera",
        minimum=1.0,
        maximum=179.0,
    )
    near_clip = Property(0.05, value_type=float, category="Camera", minimum=0.0001)
    far_clip = Property(10000.0, value_type=float, category="Camera", minimum=0.001)
    target = Property(Vec3.zero(), value_type=Vec3, category="Camera")
    up = Property(Vec3(0.0, 1.0, 0.0), value_type=Vec3, category="Camera")
    projection = Property("perspective", value_type=str, category="Camera")
    active = Property(True, value_type=bool, category="Camera")

    def __init__(self, object_id=None, name=None):
        super().__init__(object_id=object_id, name=name or "Camera")


@register_object_class("somnia.MeshObject")
class MeshObject(ModelNode):
    mesh = Property("", value_type=str, category="Rendering")
    material = Property("", value_type=str, category="Rendering")
    color = Property(Vec3(0.584, 0.0, 1.0), value_type=Vec3, category="Rendering")
    opacity = Property(
        1.0,
        value_type=float,
        category="Rendering",
        minimum=0.0,
        maximum=1.0,
    )
    visible = Property(True, value_type=bool, category="Rendering")
    wireframe = Property(False, value_type=bool, category="Rendering")
    cast_shadows = Property(True, value_type=bool, category="Lighting")
    receive_shadows = Property(True, value_type=bool, category="Lighting")

    def __init__(self, object_id=None, name=None):
        super().__init__(object_id=object_id, name=name or "MeshObject")


@register_object_class("somnia.Light")
class Light(ModelNode):
    light_type = Property("point", value_type=str, category="Lighting")
    color = Property(Vec3(1.0, 1.0, 1.0), value_type=Vec3, category="Lighting")
    intensity = Property(1.0, value_type=float, category="Lighting", minimum=0.0)
    range = Property(10.0, value_type=float, category="Lighting", minimum=0.0)
    shadows = Property(True, value_type=bool, category="Lighting")

    def __init__(self, object_id=None, name=None):
        super().__init__(object_id=object_id, name=name or "Light")


@register_object_class("somnia.RenderService")
class RenderService(Service):
    """Deprecated compatibility object; rendering now reads Scene/Environment."""

    backend = Property("null", value_type=str, category="Rendering")
    active_camera_id = Property("", value_type=str, category="Rendering")
    clear_color = Property(Vec3(0.05, 0.05, 0.08), value_type=Vec3, category="Rendering")

    def __init__(self, object_id=None, name=None):
        super().__init__(object_id=object_id, name=name or "Rendering")
