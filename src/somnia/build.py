"""Client/server export planning derived from fixed realm roots."""

from __future__ import annotations

from .model.core import OBJECT_TYPES
from .model.provider import Game, Provider, RealmRoot, RuntimeRealm


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
    def __init__(self, export_type, packages, integrated_server=False):
        self.export_type = ExportType.normalize(export_type)
        self.packages = list(packages)
        self.integrated_server = bool(integrated_server)

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
            if server_package is None or client_package is None:
                raise ValueError("Client exports require integrated server and client packages")
            if not self.integrated_server:
                raise ValueError("Client exports must mark the server as integrated")
        elif self.export_type == ExportType.DEDICATED_SERVER:
            if server_package is None or client_package is not None:
                raise ValueError("DedicatedServer exports must contain only a server package")
        elif self.export_type == ExportType.DEDICATED_CLIENT:
            if client_package is None or server_package is not None:
                raise ValueError("DedicatedClient exports must contain only a client package")
            if self.integrated_server:
                raise ValueError("DedicatedClient exports cannot contain an integrated server")

        if server_package is not None:
            if server_package.root_names() != ["Server", "Shared"]:
                raise ValueError("server packages must contain only Server and Shared roots")
        if client_package is not None:
            if client_package.root_names() != ["Shared", "Client"]:
                raise ValueError("client packages must contain only Shared and Client roots")
            forbidden = {"ServerScriptProvider", "ServerStorage", "PhysicsProvider"}
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
            "integrated_server": self.integrated_server,
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


def clone_game_for_realm(source_game, realm):
    normalized = RuntimeRealm.normalize(realm)
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

    for child in source_game.children:
        if not isinstance(child, RealmRoot):
            continue
        if not child.supports_runtime(normalized):
            continue
        clone_tree(child, result)
    return result


def create_export_plan(source_game, export_type):
    normalized = ExportType.normalize(export_type)
    packages = []
    integrated_server = False

    if normalized in (ExportType.CLIENT, ExportType.DEDICATED_SERVER):
        packages.append(
            RuntimePackage(
                RuntimeRealm.SERVER,
                clone_game_for_realm(source_game, RuntimeRealm.SERVER),
            )
        )
    if normalized in (ExportType.CLIENT, ExportType.DEDICATED_CLIENT):
        packages.append(
            RuntimePackage(
                RuntimeRealm.CLIENT,
                clone_game_for_realm(source_game, RuntimeRealm.CLIENT),
            )
        )
    if normalized == ExportType.CLIENT:
        integrated_server = True

    plan = ExportPlan(normalized, packages, integrated_server=integrated_server)
    plan.validate()
    return plan
