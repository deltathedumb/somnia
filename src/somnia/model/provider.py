"""Roblox-style singleton providers and the canonical Somnia game root."""

from __future__ import annotations

from .core import DataModel, Property, Service, register_object_class


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


@register_object_class("somnia.Provider")
class Provider(Service):
    """A user-facing singleton system directly beneath a game root.

    Providers are Somnia's equivalent of Roblox services. They are public game
    objects, while replaceable low-level implementations are called backends.
    """

    backend = Property("default", value_type=str, category="Provider")

    provider_key = "Provider"
    fixed_name = "Provider"
    hidden_by_default = False
    runtime_realms = (RuntimeRealm.SERVER, RuntimeRealm.CLIENT)

    def __init__(self, object_id=None, name=None):
        stable_id = object_id or ("provider:" + self.provider_key)
        super().__init__(object_id=stable_id, name=name or self.fixed_name)

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
            "type": getattr(cls, "__somnia_type__", cls.__name__),
        }

    def set_parent(self, parent, index=None):
        if parent is not None and not isinstance(parent, DataModel):
            raise ValueError("providers must be direct children of a DataModel")
        return super().set_parent(parent, index=index)


@register_object_class("somnia.Game")
class Game(DataModel):
    """Canonical authoring/runtime root containing Somnia providers."""

    realm = Property(RuntimeRealm.PROJECT, value_type=str, category="Runtime")

    def __init__(self, object_id=None, name=None, realm=RuntimeRealm.PROJECT):
        super().__init__(object_id=object_id, name=name or "Game")
        self.realm = RuntimeRealm.normalize(realm)

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
        if not provider_type.supports_realm(self.realm):
            raise ValueError(
                provider_type.provider_key
                + " is unavailable in the "
                + self.realm
                + " realm"
            )
        provider = provider_type()
        self.add_child(provider)
        return provider

    def install_default_providers(self):
        from .providers import canonical_provider_types

        for provider_type in canonical_provider_types():
            if provider_type.supports_realm(self.realm):
                self.ensure_provider(provider_type)
        return self

    def providers(self, include_hidden=True):
        result = []
        for child in self.children:
            if isinstance(child, Provider):
                if include_hidden or not child.hidden_by_default:
                    result.append(child)
        return result
