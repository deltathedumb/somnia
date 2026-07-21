"""Realm roots, singleton providers, and the canonical Somnia game root."""

from __future__ import annotations

from .core import DataModel, Property, Service, SomniaObject, register_object_class


class RuntimeRealm:
    """Logical runtime realms used for provider and export partitioning."""

    PROJECT = "project"
    EDITOR = "editor"
    SERVER = "server"
    CLIENT = "client"

    @classmethod
    def normalize(cls, value):
        normalized = str(value or cls.PROJECT).lower()
        if normalized not in (
            cls.PROJECT,
            cls.EDITOR,
            cls.SERVER,
            cls.CLIENT,
        ):
            raise ValueError("unsupported Somnia runtime realm: " + normalized)
        return normalized


class RealmKey:
    """Authoring hierarchy roots. Shared is packaged into both runtimes."""

    SERVER = "server"
    SHARED = "shared"
    CLIENT = "client"

    @classmethod
    def normalize(cls, value):
        normalized = str(value).lower()
        if normalized not in (cls.SERVER, cls.SHARED, cls.CLIENT):
            raise ValueError("unsupported Somnia hierarchy realm: " + normalized)
        return normalized


@register_object_class("somnia.RealmRoot")
class RealmRoot(SomniaObject):
    """Fixed top-level container for one authored packaging realm."""

    name = Property("Realm", value_type=str, category="Identity", read_only=True)
    enabled = Property(True, value_type=bool, category="Behavior", read_only=True)
    archivable = Property(False, value_type=bool, category="Behavior", read_only=True)

    realm_key = "realm"
    fixed_name = "Realm"
    runtime_realms = ()

    def __init__(self, object_id=None, name=None):
        stable_id = object_id or ("realm:" + self.realm_key)
        super().__init__(object_id=stable_id, name=self.fixed_name)

    @classmethod
    def supports_runtime(cls, realm):
        normalized = RuntimeRealm.normalize(realm)
        if normalized in (RuntimeRealm.PROJECT, RuntimeRealm.EDITOR):
            return True
        return normalized in cls.runtime_realms

    def apply_serialized_properties(self, values):
        filtered = dict(values)
        filtered.pop("name", None)
        filtered.pop("enabled", None)
        filtered.pop("archivable", None)
        super().apply_serialized_properties(filtered)
        self._loading = True
        try:
            self.name = self.fixed_name
            self.enabled = True
            self.archivable = False
        finally:
            self._loading = False

    def set_parent(self, parent, index=None):
        if parent is None and self.parent is not None:
            raise ValueError("canonical realm roots cannot be detached")
        if parent is not None and not isinstance(parent, Game):
            raise ValueError("realm roots must be direct children of Game")
        return super().set_parent(parent, index=index)

    def add_child(self, child, index=None):
        if not isinstance(child, (Provider, Service)):
            raise ValueError("realm roots may contain only providers and internal services")
        return super().add_child(child, index=index)

    def get_provider(self, provider_type_or_name, create=True):
        from .providers import resolve_provider_type

        provider_type = resolve_provider_type(provider_type_or_name)
        for child in self.children:
            if isinstance(child, provider_type):
                return child
        if not create:
            return None
        return self.ensure_provider(provider_type)

    def ensure_provider(self, provider_type_or_name):
        from .providers import resolve_provider_type

        provider_type = resolve_provider_type(provider_type_or_name)
        existing = self.get_provider(provider_type, create=False)
        if existing is not None:
            return existing
        if self.realm_key not in provider_type.root_keys:
            raise ValueError(
                provider_type.provider_key
                + " cannot be placed beneath the "
                + self.fixed_name
                + " root"
            )
        provider = provider_type(
            object_id=("provider:" + self.realm_key + ":" + provider_type.provider_key)
        )
        self.add_child(provider)
        return provider

    def providers(self, include_hidden=True):
        result = []
        for child in self.children:
            if isinstance(child, Provider):
                if include_hidden or not child.hidden_by_default:
                    result.append(child)
        return result

    def __getattr__(self, name):
        children = self.__dict__.get("children", [])
        for child in children:
            if isinstance(child, Provider) and name in (
                child.provider_key,
                child.fixed_name,
                type(child).__name__,
            ):
                return child
        raise AttributeError(type(self).__name__ + " has no attribute " + repr(name))


@register_object_class("somnia.Server")
class Server(RealmRoot):
    realm_key = RealmKey.SERVER
    fixed_name = "Server"
    runtime_realms = (RuntimeRealm.SERVER,)
    name = Property("Server", value_type=str, category="Identity", read_only=True)


@register_object_class("somnia.Shared")
class Shared(RealmRoot):
    realm_key = RealmKey.SHARED
    fixed_name = "Shared"
    runtime_realms = (RuntimeRealm.SERVER, RuntimeRealm.CLIENT)
    name = Property("Shared", value_type=str, category="Identity", read_only=True)


@register_object_class("somnia.Client")
class Client(RealmRoot):
    realm_key = RealmKey.CLIENT
    fixed_name = "Client"
    runtime_realms = (RuntimeRealm.CLIENT,)
    name = Property("Client", value_type=str, category="Identity", read_only=True)


def canonical_realm_root_types():
    return (Server, Shared, Client)


def resolve_realm_root_type(realm_key):
    normalized = RealmKey.normalize(realm_key)
    for root_type in canonical_realm_root_types():
        if root_type.realm_key == normalized:
            return root_type
    raise KeyError("unknown Somnia realm root: " + normalized)


@register_object_class("somnia.Provider")
class Provider(Service):
    """A user-facing singleton system beneath a fixed realm root."""

    backend = Property("default", value_type=str, category="Provider")

    provider_key = "Provider"
    fixed_name = "Provider"
    hidden_by_default = False
    runtime_realms = (RuntimeRealm.SERVER, RuntimeRealm.CLIENT)
    root_keys = (RealmKey.SHARED,)
    default_root_key = RealmKey.SHARED

    def __init__(self, object_id=None, name=None):
        stable_id = object_id or ("provider:" + self.provider_key)
        super().__init__(object_id=stable_id, name=name or self.fixed_name)

    @property
    def realm_root(self):
        return self.parent if isinstance(self.parent, RealmRoot) else None

    @property
    def game(self):
        root = self.realm_root
        return root.parent if root is not None and isinstance(root.parent, Game) else None

    @classmethod
    def supports_realm(cls, realm):
        normalized = RuntimeRealm.normalize(realm)
        if normalized in (RuntimeRealm.PROJECT, RuntimeRealm.EDITOR):
            return True
        return normalized in cls.runtime_realms

    @classmethod
    def provider_description(cls):
        return {
            "key": cls.provider_key,
            "name": cls.fixed_name,
            "hidden": cls.hidden_by_default,
            "realms": list(cls.runtime_realms),
            "roots": list(cls.root_keys),
            "type": getattr(cls, "__somnia_type__", cls.__name__),
        }

    def on_attached_to_root(self, root):
        return None

    def set_parent(self, parent, index=None):
        if parent is None and self.parent is not None:
            raise ValueError("canonical providers cannot be detached")
        if parent is not None:
            if not isinstance(parent, RealmRoot):
                raise ValueError("providers must be direct children of a realm root")
            if parent.realm_key not in self.root_keys:
                raise ValueError(
                    self.provider_key
                    + " cannot be placed beneath the "
                    + parent.fixed_name
                    + " root"
                )
        result = super().set_parent(parent, index=index)
        if parent is not None:
            self.on_attached_to_root(parent)
        return result


@register_object_class("somnia.Game")
class Game(DataModel):
    """Canonical root containing only Server, Shared, and Client children."""

    realm = Property(RuntimeRealm.PROJECT, value_type=str, category="Runtime")

    def __init__(self, object_id=None, name=None, realm=RuntimeRealm.PROJECT):
        super().__init__(object_id=object_id, name=name or "Game")
        self.realm = RuntimeRealm.normalize(realm)

    def add_child(self, child, index=None):
        if isinstance(child, Provider):
            root = self.ensure_realm_root(child.default_root_key)
            return root.add_child(child, index=index)
        if isinstance(child, Service) and not isinstance(child, RealmRoot):
            return self.ensure_realm_root(RealmKey.SHARED).add_child(child, index=index)
        if not isinstance(child, RealmRoot):
            raise ValueError("Server, Shared, and Client are the only Game children")
        existing = self.get_realm_root(child.realm_key, create=False)
        if existing is not None and existing is not child:
            raise ValueError(child.fixed_name + " realm root already exists")
        return super().add_child(child, index=index)

    def remove_child(self, child):
        if isinstance(child, RealmRoot):
            raise ValueError("canonical realm roots cannot be deleted")
        return super().remove_child(child)

    def realm_roots(self):
        result = []
        for root_type in canonical_realm_root_types():
            root = self.get_realm_root(root_type.realm_key, create=False)
            if root is not None:
                result.append(root)
        return result

    def get_realm_root(self, realm_key, create=True):
        root_type = resolve_realm_root_type(realm_key)
        for child in self.children:
            if isinstance(child, root_type):
                return child
        if not create:
            return None
        return self.ensure_realm_root(root_type.realm_key)

    def ensure_realm_root(self, realm_key):
        root_type = resolve_realm_root_type(realm_key)
        existing = self.get_realm_root(root_type.realm_key, create=False)
        if existing is not None:
            return existing
        if not root_type.supports_runtime(self.realm):
            raise ValueError(
                root_type.fixed_name + " is unavailable in the " + self.realm + " runtime"
            )
        root = root_type()
        super().add_child(root)
        return root

    @property
    def server(self):
        return self.get_realm_root(
            RealmKey.SERVER,
            create=self.realm in (
                RuntimeRealm.PROJECT,
                RuntimeRealm.EDITOR,
                RuntimeRealm.SERVER,
            ),
        )

    @property
    def shared(self):
        return self.get_realm_root(RealmKey.SHARED, create=True)

    @property
    def client(self):
        return self.get_realm_root(
            RealmKey.CLIENT,
            create=self.realm in (
                RuntimeRealm.PROJECT,
                RuntimeRealm.EDITOR,
                RuntimeRealm.CLIENT,
            ),
        )

    def get_provider(self, provider_type_or_name, create=True, realm=None):
        from .providers import resolve_provider_type

        provider_type = resolve_provider_type(provider_type_or_name)
        if realm is not None:
            root = self.get_realm_root(realm, create=create)
            if root is None:
                return None
            return root.get_provider(provider_type, create=create)

        matches = []
        for root in self.realm_roots():
            provider = root.get_provider(provider_type, create=False)
            if provider is not None:
                matches.append(provider)
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ValueError(
                provider_type.provider_key
                + " exists in multiple realms; specify server, shared, or client"
            )
        if not create:
            return None
        return self.ensure_provider(provider_type)

    def ensure_provider(self, provider_type_or_name, realm=None):
        from .providers import resolve_provider_type

        provider_type = resolve_provider_type(provider_type_or_name)
        root_key = RealmKey.normalize(realm) if realm is not None else provider_type.default_root_key
        root = self.ensure_realm_root(root_key)
        return root.ensure_provider(provider_type)

    def install_default_providers(self):
        from .providers import canonical_provider_types_for_root

        for root_type in canonical_realm_root_types():
            if not root_type.supports_runtime(self.realm):
                continue
            root = self.ensure_realm_root(root_type.realm_key)
            for provider_type in canonical_provider_types_for_root(root.realm_key):
                root.ensure_provider(provider_type)
        return self

    def providers(self, include_hidden=True, realm=None):
        if realm is not None:
            root = self.get_realm_root(realm, create=False)
            return [] if root is None else root.providers(include_hidden=include_hidden)
        result = []
        for root in self.realm_roots():
            result.extend(root.providers(include_hidden=include_hidden))
        return result

    def get_service(self, service_type):
        if isinstance(service_type, type) and issubclass(service_type, Provider):
            return self.get_provider(service_type, create=False)
        for root in self.realm_roots():
            for child in root.children:
                if isinstance(child, service_type):
                    return child
        return None

    def ensure_service(self, service_type, name=None):
        if isinstance(service_type, type) and issubclass(service_type, Provider):
            return self.get_provider(service_type)
        existing = self.get_service(service_type)
        if existing is not None:
            return existing
        service = service_type(name=name)
        self.shared.add_child(service)
        return service
