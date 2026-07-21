"""Canonical provider classes used by Somnia projects and runtime exports."""

from __future__ import annotations

from somnia.math import Vec3

from .core import DataModel, Property, register_object_class
from .provider import Game, Provider, RuntimeRealm
from .scene import Environment, Scene


class ContainerProvider(Provider):
    """Provider whose primary purpose is owning project objects."""


class ScriptContainerProvider(ContainerProvider):
    def scripts(self):
        from .scripting import PythonScript

        return [
            obj
            for obj in self.walk(include_self=False)
            if isinstance(obj, PythonScript)
        ]


@register_object_class("somnia.PhysicsProvider")
class PhysicsProvider(Provider):
    provider_key = "PhysicsProvider"
    fixed_name = "PhysicsProvider"
    hidden_by_default = True
    runtime_realms = (RuntimeRealm.SERVER, RuntimeRealm.CLIENT)

    gravity = Property(Vec3(0.0, -9.81, 0.0), value_type=Vec3, category="Physics")
    solver_substeps = Property(1, value_type=int, category="Physics", minimum=1)
    collision_groups = Property({}, value_type=dict, category="Physics")


@register_object_class("somnia.ServerScriptProvider")
class ServerScriptProvider(ScriptContainerProvider):
    provider_key = "ServerScriptProvider"
    fixed_name = "ServerScriptProvider"
    runtime_realms = (RuntimeRealm.SERVER,)


@register_object_class("somnia.ServerStorage")
class ServerStorage(ContainerProvider):
    provider_key = "ServerStorage"
    fixed_name = "ServerStorage"
    runtime_realms = (RuntimeRealm.SERVER,)


@register_object_class("somnia.SharedStorage")
class SharedStorage(ContainerProvider):
    provider_key = "SharedStorage"
    fixed_name = "SharedStorage"
    runtime_realms = (RuntimeRealm.SERVER, RuntimeRealm.CLIENT)


@register_object_class("somnia.ClientStorage")
class ClientStorage(ContainerProvider):
    provider_key = "ClientStorage"
    fixed_name = "ClientStorage"
    runtime_realms = (RuntimeRealm.CLIENT,)


@register_object_class("somnia.PlayerProvider")
class PlayerProvider(ContainerProvider):
    provider_key = "PlayerProvider"
    fixed_name = "PlayerProvider"
    runtime_realms = (RuntimeRealm.SERVER, RuntimeRealm.CLIENT)

    maximum_players = Property(1, value_type=int, category="Players", minimum=1)
    local_player_id = Property("", value_type=str, category="Players")


@register_object_class("somnia.PlayerScriptProvider")
class PlayerScriptProvider(ScriptContainerProvider):
    provider_key = "PlayerScriptProvider"
    fixed_name = "PlayerScriptProvider"
    runtime_realms = (RuntimeRealm.CLIENT,)


@register_object_class("somnia.PlayerUIProvider")
class PlayerUIProvider(ContainerProvider):
    provider_key = "PlayerUIProvider"
    fixed_name = "PlayerUIProvider"
    runtime_realms = (RuntimeRealm.CLIENT,)


@register_object_class("somnia.NetworkProvider")
class NetworkProvider(Provider):
    provider_key = "NetworkProvider"
    fixed_name = "NetworkProvider"
    hidden_by_default = True
    runtime_realms = (RuntimeRealm.SERVER, RuntimeRealm.CLIENT)

    transport_backend = Property("local", value_type=str, category="Networking")
    remote_endpoint = Property("", value_type=str, category="Networking")
    connected = Property(
        False,
        value_type=bool,
        serializable=False,
        category="Networking",
        read_only=True,
    )

    def __init__(self, object_id=None, name=None):
        super().__init__(object_id=object_id, name=name)
        self._transport = None

    def attach_transport(self, transport):
        self._transport = transport
        self._loading = True
        self.connected = bool(transport is not None and transport.connected)
        self.transport_backend = (
            transport.backend_name if transport is not None else "none"
        )
        self._loading = False
        return self

    def send(self, channel, payload=None):
        from somnia.networking import NetworkPacket

        if self._transport is None or not self._transport.connected:
            raise ConnectionError("NetworkProvider is not connected")
        sender = self.parent.realm if isinstance(self.parent, Game) else ""
        packet = NetworkPacket(channel, payload=payload, sender=sender)
        self._transport.send(packet)
        return packet

    def receive(self):
        if self._transport is None:
            return []
        packets = self._transport.receive()
        self._loading = True
        self.connected = self._transport.connected
        self._loading = False
        return packets

    def close(self):
        if self._transport is not None:
            self._transport.close()
        self._transport = None
        self._loading = True
        self.connected = False
        self._loading = False


@register_object_class("somnia.HttpProvider")
class HttpProvider(Provider):
    provider_key = "HttpProvider"
    fixed_name = "HttpProvider"
    hidden_by_default = True
    runtime_realms = (RuntimeRealm.SERVER, RuntimeRealm.CLIENT)

    requests_enabled = Property(False, value_type=bool, category="HTTP")
    user_agent = Property("SomniaEngine", value_type=str, category="HTTP")


@register_object_class("somnia.AnimationProvider")
class AnimationProvider(Provider):
    provider_key = "AnimationProvider"
    fixed_name = "AnimationProvider"
    hidden_by_default = True
    runtime_realms = (RuntimeRealm.SERVER, RuntimeRealm.CLIENT)

    default_frame_rate = Property(60.0, value_type=float, category="Animation", minimum=1.0)


@register_object_class("somnia.AudioProvider")
class AudioProvider(Provider):
    provider_key = "AudioProvider"
    fixed_name = "AudioProvider"
    hidden_by_default = True
    runtime_realms = (RuntimeRealm.CLIENT,)

    master_volume = Property(
        1.0,
        value_type=float,
        category="Audio",
        minimum=0.0,
        maximum=1.0,
    )


@register_object_class("somnia.InputProvider")
class InputProvider(Provider):
    provider_key = "InputProvider"
    fixed_name = "InputProvider"
    hidden_by_default = True
    runtime_realms = (RuntimeRealm.CLIENT,)

    mouse_sensitivity = Property(1.0, value_type=float, category="Input", minimum=0.0)


@register_object_class("somnia.TimeProvider")
class TimeProvider(Provider):
    provider_key = "TimeProvider"
    fixed_name = "TimeProvider"
    hidden_by_default = True
    runtime_realms = (RuntimeRealm.SERVER, RuntimeRealm.CLIENT)

    time_scale = Property(1.0, value_type=float, category="Time", minimum=0.0)
    fixed_rate = Property(60.0, value_type=float, category="Time", minimum=1.0)


@register_object_class("somnia.Assets")
class Assets(ContainerProvider):
    provider_key = "Assets"
    fixed_name = "Assets"
    runtime_realms = (RuntimeRealm.SERVER, RuntimeRealm.CLIENT)

    root_path = Property("assets", value_type=str, category="Assets")


@register_object_class("somnia.NavigationProvider")
class NavigationProvider(Provider):
    provider_key = "NavigationProvider"
    fixed_name = "NavigationProvider"
    hidden_by_default = True
    runtime_realms = (RuntimeRealm.SERVER,)

    agent_radius = Property(0.5, value_type=float, category="Navigation", minimum=0.0)
    agent_height = Property(2.0, value_type=float, category="Navigation", minimum=0.0)


@register_object_class("somnia.LocalizationProvider")
class LocalizationProvider(Provider):
    provider_key = "LocalizationProvider"
    fixed_name = "LocalizationProvider"
    hidden_by_default = True
    runtime_realms = (RuntimeRealm.CLIENT,)

    default_locale = Property("en-US", value_type=str, category="Localization")


_CANONICAL_PROVIDER_TYPES = (
    Scene,
    Environment,
    PhysicsProvider,
    ServerScriptProvider,
    ServerStorage,
    SharedStorage,
    ClientStorage,
    PlayerProvider,
    PlayerScriptProvider,
    PlayerUIProvider,
    NetworkProvider,
    HttpProvider,
    AnimationProvider,
    AudioProvider,
    InputProvider,
    TimeProvider,
    Assets,
    NavigationProvider,
    LocalizationProvider,
)

_PROVIDER_ALIASES = {
    "World": "Scene",
    "Workspace": "Scene",
    "Lighting": "Environment",
    "ServerScriptService": "ServerScriptProvider",
    "StarterPlayerScripts": "PlayerScriptProvider",
}


def canonical_provider_types():
    return _CANONICAL_PROVIDER_TYPES


def resolve_provider_type(provider_type_or_name):
    if isinstance(provider_type_or_name, type) and issubclass(provider_type_or_name, Provider):
        return provider_type_or_name
    requested = str(provider_type_or_name)
    requested = _PROVIDER_ALIASES.get(requested, requested)
    for provider_type in _CANONICAL_PROVIDER_TYPES:
        if requested in (
            provider_type.provider_key,
            provider_type.fixed_name,
            provider_type.__name__,
            getattr(provider_type, "__somnia_type__", ""),
        ):
            return provider_type
    raise KeyError("unknown Somnia provider: " + requested)


def get_provider(data_model, provider_type_or_name, create=True):
    provider_type = resolve_provider_type(provider_type_or_name)
    if isinstance(data_model, Game):
        return data_model.get_provider(provider_type, create=create)
    for child in data_model.children:
        if isinstance(child, provider_type):
            return child
    if not create:
        return None
    provider = provider_type()
    data_model.add_child(provider)
    return provider


def install_canonical_providers(data_model, realm=RuntimeRealm.PROJECT):
    normalized = RuntimeRealm.normalize(realm)
    if isinstance(data_model, Game):
        data_model.realm = normalized
        return data_model.install_default_providers()
    if not isinstance(data_model, DataModel):
        raise TypeError("providers require a DataModel root")
    for provider_type in _CANONICAL_PROVIDER_TYPES:
        if provider_type.supports_realm(normalized):
            get_provider(data_model, provider_type, create=True)
    return data_model
