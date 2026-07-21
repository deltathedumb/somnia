from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from somnia import (
    AssetDatabase,
    AssetKind,
    Engine,
    Game,
    InputEvent,
    InputEventType,
    InputProvider,
    QueueInputBackend,
    RuntimeRealm,
    asset_id_for_path,
    normalize_asset_path,
)


class InputFrameTests(unittest.TestCase):
    def test_engine_publishes_deterministic_input_frames(self) -> None:
        backend = QueueInputBackend()
        backend.submit(
            events=[
                InputEvent(
                    InputEventType.BUTTON_DOWN,
                    code="KeyW",
                    value=1.0,
                    device="keyboard",
                ),
                InputEvent(
                    InputEventType.AXIS,
                    code="MoveX",
                    value=0.75,
                    device="gamepad",
                ),
                InputEvent(
                    InputEventType.POINTER,
                    code="Pointer",
                    position=(320, 180),
                    device="mouse",
                ),
                InputEvent(
                    InputEventType.WHEEL,
                    code="WheelY",
                    value=2.0,
                    device="mouse",
                ),
                InputEvent(
                    InputEventType.TEXT,
                    text="s",
                    device="keyboard",
                ),
            ]
        )
        engine = Engine(
            Game(realm=RuntimeRealm.CLIENT),
            realm=RuntimeRealm.CLIENT,
            input_backend=backend,
        )
        provider = engine.get_provider(InputProvider)
        began = []
        changed = []
        provider.input_began.connect(lambda _provider, event: began.append(event.code))
        provider.input_changed.connect(
            lambda _provider, event: changed.append(event.event_type)
        )

        engine.frame()

        self.assertEqual(engine.input_frame.frame_number, 1)
        self.assertEqual(provider.backend_name, "queue")
        self.assertEqual(provider.frame_number, 1)
        self.assertTrue(provider.is_down("KeyW"))
        self.assertEqual(provider.axis("MoveX"), 0.75)
        self.assertEqual(provider.pointer, [320.0, 180.0])
        self.assertEqual(provider.wheel_delta, 2.0)
        self.assertEqual(provider.text_input, "s")
        self.assertEqual(began, ["KeyW"])
        self.assertEqual(
            changed,
            [
                InputEventType.AXIS,
                InputEventType.POINTER,
                InputEventType.WHEEL,
                InputEventType.TEXT,
            ],
        )

        engine.frame()
        self.assertEqual(provider.frame_number, 2)
        self.assertTrue(provider.is_down("KeyW"))
        self.assertEqual(provider.wheel_delta, 0.0)
        self.assertEqual(provider.text_input, "")
        engine.shutdown()

    def test_button_release_updates_held_state_and_emits_end(self) -> None:
        backend = QueueInputBackend()
        backend.submit(
            events=[InputEvent(InputEventType.BUTTON_DOWN, code="MouseLeft")]
        )
        backend.submit(
            events=[InputEvent(InputEventType.BUTTON_UP, code="MouseLeft")]
        )
        engine = Engine(
            Game(realm=RuntimeRealm.CLIENT),
            realm=RuntimeRealm.CLIENT,
            input_backend=backend,
        )
        provider = engine.get_provider(InputProvider)
        ended = []
        provider.input_ended.connect(lambda _provider, event: ended.append(event.code))

        engine.frame()
        self.assertTrue(provider.is_down("MouseLeft"))
        engine.frame()
        self.assertFalse(provider.is_down("MouseLeft"))
        self.assertEqual(ended, ["MouseLeft"])


class AssetDatabaseTests(unittest.TestCase):
    def test_refresh_adds_updates_and_removes_stable_asset_records(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary)
            asset_root = project_root / "assets"
            (asset_root / "scripts").mkdir(parents=True)
            (asset_root / "textures").mkdir(parents=True)
            script_path = asset_root / "scripts" / "player.py"
            texture_path = asset_root / "textures" / "stone.png"
            script_path.write_text("print('first')\n", encoding="utf-8")
            texture_path.write_bytes(b"not-a-real-png")

            engine = Engine(Game())
            database = AssetDatabase.from_data_model(
                engine.data_model,
                project_root=project_root,
            )
            first = database.refresh()
            records = database.provider.asset_records()

            self.assertEqual(len(first.added), 2)
            self.assertEqual(
                [record.source_path for record in records],
                ["scripts/player.py", "textures/stone.png"],
            )
            script = database.provider.find_asset("scripts/player.py")
            texture = database.provider.find_asset("textures/stone.png")
            self.assertEqual(script.kind, AssetKind.SCRIPT)
            self.assertEqual(texture.kind, AssetKind.TEXTURE)
            self.assertEqual(script.asset_id, asset_id_for_path("scripts/player.py"))
            stable_object_id = script.object_id
            old_hash = script.content_hash

            script_path.write_text("print('second')\n", encoding="utf-8")
            second = database.refresh()
            script = database.provider.find_asset("scripts/player.py")
            self.assertIn(script.asset_id, second.updated)
            self.assertEqual(script.object_id, stable_object_id)
            self.assertNotEqual(script.content_hash, old_hash)

            texture_path.unlink()
            third = database.refresh()
            self.assertEqual(third.removed, [texture.asset_id])
            self.assertIsNone(database.provider.find_asset("textures/stone.png"))

    def test_asset_paths_are_portable_and_cannot_escape_the_root(self) -> None:
        self.assertEqual(normalize_asset_path("./models\\cube.glb"), "models/cube.glb")
        with self.assertRaises(ValueError):
            normalize_asset_path("../secret.txt")
        with self.assertRaises(ValueError):
            normalize_asset_path("models/../../secret.txt")


if __name__ == "__main__":
    unittest.main()
