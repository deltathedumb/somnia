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
        self.assertEqual(len({
            server_assets.object_id,
            shared_assets.object_id,
            client_assets.object_id,
        }), 3)
        with self.assertRaises(ValueError):
            engine.get_provider(Assets)

    def test_explorer_hides_only_hidden_providers_by_default(self) -> None:
        engine = Engine(Game())
        editor = EditorSession(engine)
        visible_names = [obj.name for obj in editor.scene_tree()]
        all_names = [obj.name for obj in editor.scene_tree(show_hidden_providers=True)]

        self.assertEqual(visible_names[:4], ["Game", "Server", "ServerScriptProvider", "ServerStorage"])
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

    def test_dedicated_client_contains_no_server_package_or_secrets(self) -> None:
        engine = Engine(Game())
        server_storage = engine.get_provider(ServerStorage)
        server_storage.add_child(Folder(name="DatabaseSecrets"))
        client_storage = engine.get_provider(ClientStorage)
        client_storage.add_child(Folder(name="ClientEffects"))

        plan = engine.create_export_plan(ExportType.DEDICATED_CLIENT)
        client = plan.package_for("client")

        self.assertIsNone(plan.package_for("server"))
        self.assertFalse(plan.integrated_server)
        self.assertEqual(client.root_names(), ["Shared", "Client"])
        self.assertNotIn("ServerStorage", client.provider_names())
        self.assertNotIn("ServerScriptProvider", client.provider_names())
        self.assertNotIn("PhysicsProvider", client.provider_names())
        self.assertIn("ClientStorage", client.provider_names())
        self.assertIn("Shared.Assets", client.provider_paths())
        self.assertIn("Client.Assets", client.provider_paths())
        self.assertIsNone(client.data_model.find_first("DatabaseSecrets"))
        self.assertIsNotNone(client.data_model.find_first("ClientEffects"))

    def test_client_export_contains_separate_integrated_server_and_client(self) -> None:
        engine = Engine(Game())
        plan = engine.create_export_plan(ExportType.CLIENT)
        server = plan.package_for("server")
        client = plan.package_for("client")

        self.assertTrue(plan.integrated_server)
        self.assertIsNotNone(server)
        self.assertIsNotNone(client)
        self.assertIsNot(server.data_model, client.data_model)
        self.assertEqual(server.root_names(), ["Server", "Shared"])
        self.assertEqual(client.root_names(), ["Shared", "Client"])
        self.assertIn("ServerScriptProvider", server.provider_names())
        self.assertNotIn("PlayerUIProvider", server.provider_names())
        self.assertIn("PlayerUIProvider", client.provider_names())
        self.assertNotIn("ServerScriptProvider", client.provider_names())

    def test_client_play_connects_separate_realms_through_network_provider(self) -> None:
        authoring_engine = Engine(Game())
        client_engine = authoring_engine.clone_for_play()
        server_engine = client_engine.integrated_server

        client_network = client_engine.get_provider(NetworkProvider)
        server_network = server_engine.get_provider(NetworkProvider)

        self.assertTrue(client_network.connected)
        self.assertTrue(server_network.connected)
        self.assertEqual(client_network.transport_backend, "local")
        self.assertEqual(server_network.transport_backend, "local")

        client_network.send("JoinRequest", {"name": "Mabel"})
        server_packets = server_network.receive()
        self.assertEqual(len(server_packets), 1)
        self.assertEqual(server_packets[0].channel, "JoinRequest")
        self.assertEqual(server_packets[0].payload, {"name": "Mabel"})
        self.assertEqual(server_packets[0].sender, "client")

        server_network.send("JoinAccepted", {"player_id": "local"})
        client_packets = client_network.receive()
        self.assertEqual(client_packets[0].channel, "JoinAccepted")
        self.assertEqual(client_packets[0].sender, "server")

        client_engine.shutdown()
        self.assertFalse(client_network.connected)
        self.assertFalse(server_network.connected)

    def test_dedicated_server_omits_client_root(self) -> None:
        engine = Engine(Game())
        plan = engine.create_export_plan(ExportType.DEDICATED_SERVER)
        server = plan.package_for("server")

        self.assertIsNotNone(server)
        self.assertIsNone(plan.package_for("client"))
        self.assertEqual(server.root_names(), ["Server", "Shared"])
        self.assertIn("ServerStorage", server.provider_names())
        self.assertIn("PhysicsProvider", server.provider_names())
        self.assertNotIn("ClientStorage", server.provider_names())
        self.assertNotIn("PlayerUIProvider", server.provider_names())

    def test_all_provider_children_are_provider_objects(self) -> None:
        engine = Engine(Game())
        for root in engine.data_model.realm_roots():
            for provider in root.providers():
                self.assertIsInstance(provider, Provider)


if __name__ == "__main__":
    unittest.main()
