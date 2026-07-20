from __future__ import annotations

import unittest

from somnia import (
    ClientStorage,
    Engine,
    ExportType,
    Game,
    PhysicsProvider,
    PlayerUIProvider,
    Scene,
    ServerScriptProvider,
    ServerStorage,
    SharedStorage,
)
from somnia.editor import EditorSession
from somnia.model import Folder, Provider, canonical_provider_types


class ProviderAndExportTests(unittest.TestCase):
    def test_project_installs_the_selected_provider_set(self) -> None:
        engine = Engine(Game())
        expected = [provider_type.provider_key for provider_type in canonical_provider_types()]
        actual = [provider.provider_key for provider in engine.data_model.providers()]
        self.assertEqual(actual, expected)

        physics = engine.get_provider(PhysicsProvider)
        self.assertTrue(physics.hidden_by_default)
        self.assertEqual(physics.object_id, "provider:PhysicsProvider")
        self.assertIs(physics.parent, engine.data_model)

    def test_explorer_hides_only_hidden_providers_by_default(self) -> None:
        engine = Engine(Game())
        editor = EditorSession(engine)
        visible_names = [obj.name for obj in editor.scene_tree()]
        all_names = [obj.name for obj in editor.scene_tree(show_hidden_providers=True)]

        self.assertIn("Scene", visible_names)
        self.assertIn("ServerStorage", visible_names)
        self.assertIn("Assets", visible_names)
        self.assertNotIn("PhysicsProvider", visible_names)
        self.assertIn("PhysicsProvider", all_names)

    def test_providers_are_root_singletons(self) -> None:
        engine = Engine(Game())
        scene = engine.get_provider(Scene)
        self.assertIs(scene, engine.get_provider("Workspace"))
        self.assertIs(scene, engine.get_provider("Scene"))

        storage = engine.get_provider(SharedStorage)
        with self.assertRaises(ValueError):
            scene.set_parent(storage)

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
        self.assertNotIn("ServerStorage", client.provider_names())
        self.assertNotIn("ServerScriptProvider", client.provider_names())
        self.assertIn("ClientStorage", client.provider_names())
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
        self.assertIn("ServerScriptProvider", server.provider_names())
        self.assertNotIn("PlayerUIProvider", server.provider_names())
        self.assertIn("PlayerUIProvider", client.provider_names())
        self.assertNotIn("ServerScriptProvider", client.provider_names())

    def test_dedicated_server_omits_client_only_providers(self) -> None:
        engine = Engine(Game())
        plan = engine.create_export_plan(ExportType.DEDICATED_SERVER)
        server = plan.package_for("server")

        self.assertIsNotNone(server)
        self.assertIsNone(plan.package_for("client"))
        self.assertIn("ServerStorage", server.provider_names())
        self.assertNotIn("ClientStorage", server.provider_names())
        self.assertNotIn("PlayerUIProvider", server.provider_names())

    def test_all_root_provider_children_are_provider_objects(self) -> None:
        engine = Engine(Game())
        for provider in engine.data_model.providers():
            self.assertIsInstance(provider, Provider)


if __name__ == "__main__":
    unittest.main()
