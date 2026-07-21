"""Export planning derived from Somnia's fixed Server, Shared, and Client roots."""

from __future__ import annotations

from .model.core import OBJECT_TYPES
from .model.provider import Game, Provider, RealmKey, RealmRoot, RuntimeRealm


class ExportType:
    CLIENT = "Client"
    DEDICATED_SERVER = "DedicatedServer"
    DEDICATED_CLIENT = "DedicatedClient"

    @classmethod
    def normalize(cls, value):
        requested = str(value)
        for candidate in (
            cls.CLIENT,
            cls.DEDICATED_SERVER,
            cls.DEDICATED_CLIENT,
        ):
            if requested.lower() == candidate.lower():
                return candidate
        raise ValueError("unsupported Somnia export type: " + requested)


class RuntimePackage:
    def __init__(self, realm, data_model):
        self.realm = RuntimeRealm.normalize(realm)
        self.data_model = data_model

    def root_names(self):
        return [root.name for root in self.data_model.realm_roots()]

    def provider_names(self):
        return [provider.provider_key for provider in self.data_model.providers()]

    def provider_paths(self):
        return [
            provider.realm_root.name + "." + provider.provider_key
            for provider in self.data_model.providers()
        ]


class ExportPlan:
    def __init__(self, export_type, packages):
        self.export_type = ExportType.normalize(export_type)
        self.packages = list(packages)

    def package_for(self, realm):
        normalized = RuntimeRealm.normalize(realm)
        for package in self.packages:
            if package.realm == normalized:
                return package
        return None

    def validate(self):
        server_package = self.package_for(RuntimeRealm.SERVER)
        client_package = self.package_for(RuntimeRealm.CLIENT)

        if self.export_type == ExportType.CLIENT:
            if client_package is None or server_package is not None:
                raise ValueError("Client exports must contain only a client package")
            expected_roots = ["Shared", "Client"]
            if client_package.root_names() != expected_roots:
                raise ValueError("Client exports must contain Shared and Client roots")
        elif self.export_type == ExportType.DEDICATED_CLIENT:
            if client_package is None or server_package is not None:
                raise ValueError("DedicatedClient exports must contain only a client package")
            if client_package.root_names() != ["Client"]:
                raise ValueError("DedicatedClient exports must contain only the Client root")
        elif self.export_type == ExportType.DEDICATED_SERVER:
            if server_package is None or client_package is not None:
                raise ValueError("DedicatedServer exports must contain only a server package")
            if server_package.root_names() != ["Server", "Shared"]:
                raise ValueError(
                    "DedicatedServer exports must contain Server and Shared roots"
                )

        if client_package is not None:
            forbidden = {
                "ServerScriptProvider",
                "ServerStorage",
                "PhysicsProvider",
                "NavigationProvider",
            }
            leaked = forbidden.intersection(client_package.provider_names())
            if leaked:
                raise ValueError(
                    "client package contains server-only providers: "
                    + ", ".join(sorted(leaked))
                )
        return True

    def manifest(self):
        self.validate()
        return {
            "export_type": self.export_type,
            "packages": [
                {
                    "realm": package.realm,
                    "roots": package.root_names(),
                    "providers": package.provider_paths(),
                }
                for package in self.packages
            ],
        }


def _clone_object(source):
    clone = OBJECT_TYPES.create(
        source.type_name,
        object_id=source.object_id,
        name=source.name,
    )
    clone.tags = list(source.tags)
    clone.extensions = dict(source.extensions)
    clone.extensions["source_object_id"] = source.object_id
    clone.apply_serialized_properties(source.serializable_properties())
    return clone


def clone_game_for_roots(source_game, realm, root_keys):
    normalized = RuntimeRealm.normalize(realm)
    requested_roots = [RealmKey.normalize(root_key) for root_key in root_keys]
    result = Game(name=source_game.name, realm=normalized)
    result.tags = list(source_game.tags)
    result.extensions = dict(source_game.extensions)
    result.extensions["source_object_id"] = source_game.object_id

    def clone_tree(source, parent):
        if source.type_name.startswith("somnia.editor."):
            return None
        clone = _clone_object(source)
        parent.add_child(clone)
        for child in source.children:
            clone_tree(child, clone)
        return clone

    for root_key in requested_roots:
        root = source_game.get_realm_root(root_key, create=False)
        if root is not None:
            clone_tree(root, result)
    return result


def clone_game_for_realm(source_game, realm):
    """Compatibility helper for the normal server/client runtime partitions."""
    normalized = RuntimeRealm.normalize(realm)
    if normalized == RuntimeRealm.SERVER:
        root_keys = (RealmKey.SERVER, RealmKey.SHARED)
    elif normalized == RuntimeRealm.CLIENT:
        root_keys = (RealmKey.SHARED, RealmKey.CLIENT)
    else:
        raise ValueError("runtime export clones require server or client realm")
    return clone_game_for_roots(source_game, normalized, root_keys)


def create_export_plan(source_game, export_type):
    normalized = ExportType.normalize(export_type)

    if normalized == ExportType.CLIENT:
        packages = [
            RuntimePackage(
                RuntimeRealm.CLIENT,
                clone_game_for_roots(
                    source_game,
                    RuntimeRealm.CLIENT,
                    (RealmKey.SHARED, RealmKey.CLIENT),
                ),
            )
        ]
    elif normalized == ExportType.DEDICATED_CLIENT:
        packages = [
            RuntimePackage(
                RuntimeRealm.CLIENT,
                clone_game_for_roots(
                    source_game,
                    RuntimeRealm.CLIENT,
                    (RealmKey.CLIENT,),
                ),
            )
        ]
    else:
        packages = [
            RuntimePackage(
                RuntimeRealm.SERVER,
                clone_game_for_roots(
                    source_game,
                    RuntimeRealm.SERVER,
                    (RealmKey.SERVER, RealmKey.SHARED),
                ),
            )
        ]

    plan = ExportPlan(normalized, packages)
    plan.validate()
    return plan
