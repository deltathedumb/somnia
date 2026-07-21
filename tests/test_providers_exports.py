from __future__ import annotations

import unittest

from somnia import (
    Assets,
    ClientStorage,
    Engine,
    ExportType,
    Game,
    NetworkProvider,
    PhysicsProvider,
    Scene,
    ServerStorage,
    SharedStorage,
)
from somnia.editor import EditorSession
from somnia.model import Folder, Provider, RealmRoot, canonical_provider_types


class ProviderAndExportTests(unittest.TestCase):
    def test_game_has_only_three_fixed_top_level_roots(self) -> None:
        engine = Engine(Game())
        game = engine.data_model

        self.assertEqual([child.name for child in game.children], ["Server", "Shared", "Client"])
        self.assertTrue(all(isinstance(child, RealmRoot) for child in game.children))
        self.assertIs(game.server, game.children[0])
        self.assertIs(game.shared, game.children[1])
        self.assertIs(game.client, game.children[2])

        with self.assertRaises(ValueError):
            game.add_child(Folder(name="FourthRoot"))
        with self.assertRaises(ValueError):
            game.server.set_parent(None)

    def test_project_installs_selected_providers_under_their_realms(self) -> None:
        engine = Engine(Game())
        game = engine.data_model

        expected_unique = {
            provider_type.provider_key for provider_type in canonical_provider_types()
        }
        actual_unique = {provider.provider_key for provider in game.providers()}
        self.assertEqual(actual_unique, expected_unique)
        self.assertEqual(len(actual_unique), 19)

        self.assertEqual(
            [provider.provider_key for provider in game.server.providers()],
            [
                "PhysicsProvider",
                "ServerScriptProvider",
                "ServerStorage",
                "NavigationProvider",
                "Assets",
            ],
        )
        self.assertEqual(
            [provider.provider_key for provider in game.shared.providers()],
            [
                "Scene",
                "SharedStorage",
                "PlayerProvider",
                "NetworkProvider",
                "HttpProvider",
                "AnimationProvider",
                "TimeProvider",
                "Assets",
            ],
        )
        self.assertEqual(
            [provider.provider_key for provider in game.client.providers()],
            [
                "Environment",
                "ClientStorage",
                "PlayerScriptProvider",
                "PlayerUIProvider",
                "AudioProvider",
                "InputProvider",
                "LocalizationProvider",
                "Assets",
            ],
        )

        physics = game.server.PhysicsProvider
        self.assertIs(physics, engine.get_provider(PhysicsProvider))
        self.assertTrue(physics.hidden_by_default)
        self.assertEqual(physics.object_id, "provider:server:PhysicsProvider")
        self.assertIs(physics.parent, game.server)
        self.assertIs(game.shared.Scene, engine.get_provider("Workspace"))
        self.assertIs(game.client.ClientStorage, engine.get_provider(ClientStorage))

    def test_each_realm_has_distinct_assets(self) -> None:
        engine = Engine(Game())
        game = engine.data_model

        server_assets = engine.get_provider(Assets, realm="server")
        shared_assets = engine.get_provider(Assets, realm="shared")
        client_assets = engine.get_provider(Assets, realm="client")

        self.assertIs(server_assets, game.server.Assets)
        self.assertIs(shared_assets, game.shared.Assets)
        self.assertIs(client_assets, game.client.Assets)
        self.assertEqual(server_assets.root_path, "assets/server")
        self.assertEqual(shared_assets.root_path, "assets/shared")
        self.assertEqual(client_assets.root_path, "assets/client")
        self.assertEqual(
            len(
                {
                    server_assets.object_id,
                    shared_assets.object_id,
                    client_assets.object_id,
                }
            ),
            3,
        )
        with self.assertRaises(ValueError):
            engine.get_provider(Assets)

    def test_explorer_hides_only_hidden_providers_by_default(self) -> None:
        engine = Engine(Game())
        editor = EditorSession(engine)
        visible_names = [obj.name for obj in editor.scene_tree()]
        all_names = [obj.name for obj in editor.scene_tree(show_hidden_providers=True)]

        self.assertEqual(
            visible_names[:4],
            ["Game", "Server", "ServerScriptProvider", "ServerStorage"],
        )
        self.assertIn("Shared", visible_names)
        self.assertIn("Client", visible_names)
        self.assertEqual(visible_names.count("Assets"), 3)
        self.assertNotIn("PhysicsProvider", visible_names)
        self.assertIn("PhysicsProvider", all_names)
        self.assertNotIn("Editor", visible_names)

    def test_providers_are_realm_singletons(self) -> None:
        engine = Engine(Game())
        scene = engine.get_provider(Scene)
        self.assertIs(scene, engine.get_provider("Workspace"))
        self.assertIs(scene, engine.data_model.shared.Scene)

        storage = engine.get_provider(SharedStorage)
        with self.assertRaises(ValueError):
            scene.set_parent(storage)
        with self.assertRaises(ValueError):
            scene.set_parent(engine.data_model.server)

    def test_legacy_flat_provider_additions_are_routed_to_realms(self) -> None:
        game = Game()
        storage = ServerStorage()
        game.add_child(storage)

        self.assertEqual([child.name for child in game.children], ["Server"])
        self.assertIs(storage.parent, game.server)
        self.assertIs(game.server.ServerStorage, storage)

    def test_client_export_contains_shared_and_client_only(self) -> None:
        engine = Engine(Game())
        plan = engine.create_export_plan(ExportType.CLIENT)
        client = plan.package_for("client")

        self.assertIsNone(plan.package_for("server"))
        self.assertIsNotNone(client)
        self.assertEqual(client.root_names(), ["Shared", "Client"])
        self.assertIn("Shared.Scene", client.provider_paths())
        self.assertIn("Shared.NetworkProvider", client.provider_paths())
        self.assertIn("Client.InputProvider", client.provider_paths())
        self.assertNotIn("ServerStorage", client.provider_names())
        self.assertNotIn("PhysicsProvider", client.provider_names())

    def test_dedicated_client_contains_only_client_root(self) -> None:
        engine = Engine(Game())
        server_storage = engine.get_provider(ServerStorage)
        server_storage.add_child(Folder(name="DatabaseSecrets"))
        shared_storage = engine.get_provider(SharedStorage)
        shared_storage.add_child(Folder(name="SharedContent"))
        client_storage = engine.get_provider(ClientStorage)
        client_storage.add_child(Folder(name="ClientEffects"))

        plan = engine.create_export_plan(ExportType.DEDICATED_CLIENT)
        client = plan.package_for("client")

        self.assertIsNone(plan.package_for("server"))
        self.assertEqual(client.root_names(), ["Client"])
        self.assertNotIn("ServerStorage", client.provider_names())
        self.assertNotIn("SharedStorage", client.provider_names())
        self.assertNotIn("NetworkProvider", client.provider_names())
        self.assertIn("ClientStorage", client.provider_names())
        self.assertNotIn("Shared.Assets", client.provider_paths())
        self.assertIn("Client.Assets", client.provider_paths())
        self.assertIsNone(client.data_model.find_first("DatabaseSecrets"))
        self.assertIsNone(client.data_model.find_first("SharedContent"))
        self.assertIsNotNone(client.data_model.find_first("ClientEffects"))

    def test_runtime_preserves_dedicated_client_root_set(self) -> None:
        authoring = Engine(Game())
        package = authoring.create_export_plan(
            ExportType.DEDICATED_CLIENT
        ).package_for("client")

        runtime = Engine(data_model=package.data_model, realm="client")

        self.assertEqual(
            [root.name for root in runtime.data_model.realm_roots()],
            ["Client"],
        )
        self.assertIsNone(runtime.data_model.get_realm_root("shared", create=False))
        self.assertIsNone(runtime.get_provider(NetworkProvider, create=False))

    def test_client_play_uses_shared_and_client_roots(self) -> None:
        authoring_engine = Engine(Game())
        client_engine = authoring_engine.clone_for_play()

        self.assertEqual(
            [root.name for root in client_engine.data_model.realm_roots()],
            ["Shared", "Client"],
        )
        self.assertIsNotNone(client_engine.get_provider(Scene))
        self.assertIsNotNone(client_engine.get_provider(NetworkProvider))
        self.assertIsNone(client_engine.data_model.get_realm_root("server", create=False))

    def test_dedicated_server_contains_server_and_shared(self) -> None:
        engine = Engine(Game())
        plan = engine.create_export_plan(ExportType.DEDICATED_SERVER)
        server = plan.package_for("server")

        self.assertIsNotNone(server)
        self.assertIsNone(plan.package_for("client"))
        self.assertEqual(server.root_names(), ["Server", "Shared"])
        self.assertIn("ServerStorage", server.provider_names())
        self.assertIn("PhysicsProvider", server.provider_names())
        self.assertIn("SharedStorage", server.provider_names())
        self.assertNotIn("ClientStorage", server.provider_names())
        self.assertNotIn("PlayerUIProvider", server.provider_names())

    def test_export_manifests_match_the_root_contract(self) -> None:
        engine = Engine(Game())

        self.assertEqual(
            engine.create_export_plan(ExportType.CLIENT).manifest()["packages"][0]["roots"],
            ["Shared", "Client"],
        )
        self.assertEqual(
            engine.create_export_plan(ExportType.DEDICATED_CLIENT)
            .manifest()["packages"][0]["roots"],
            ["Client"],
        )
        self.assertEqual(
            engine.create_export_plan(ExportType.DEDICATED_SERVER)
            .manifest()["packages"][0]["roots"],
            ["Server", "Shared"],
        )

    def test_all_provider_children_are_provider_objects(self) -> None:
        engine = Engine(Game())
        for root in engine.data_model.realm_roots():
            for provider in root.providers():
                self.assertIsInstance(provider, Provider)


if __name__ == "__main__":
    unittest.main()
