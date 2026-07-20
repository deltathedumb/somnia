from __future__ import annotations

import unittest

from somnia import DataModel, ModelNode, Property, World, register_object_class
from somnia.editor import EditorSession
from somnia.runtime import Engine


@register_object_class("tests.Door")
class Door(ModelNode):
    open_speed = Property(
        2.0,
        value_type=float,
        category="Door",
        minimum=0.0,
    )
    locked = Property(False, value_type=bool, category="Door")


class ObjectModelTests(unittest.TestCase):
    def test_custom_object_class_uses_reflection_and_editor_history(self) -> None:
        engine = Engine(DataModel(object_id="data", name="Game"))
        editor = EditorSession(engine)
        world = engine.data_model.get_service(World)

        door = editor.create_object("tests.Door", world, name="FrontDoor")
        self.assertIsInstance(door, Door)
        self.assertIs(door.parent, world)
        self.assertEqual(door.open_speed, 2.0)

        rows = {row["name"]: row for row in editor.inspect_object(door)}
        self.assertEqual(rows["open_speed"]["category"], "Door")

        editor.set_property(door, "open_speed", 4.5)
        self.assertEqual(door.open_speed, 4.5)
        self.assertEqual(editor.history.undo_count, 2)

        editor.history.undo()
        self.assertEqual(door.open_speed, 2.0)
        editor.history.redo()
        self.assertEqual(door.open_speed, 4.5)

    def test_editor_and_runtime_use_same_hierarchy_shape(self) -> None:
        engine = Engine(DataModel(object_id="data", name="Game"))
        editor = EditorSession(engine)
        world = engine.data_model.get_service(World)
        door = editor.create_object("tests.Door", world, name="Door")
        door.locked = True

        play_engine = editor.play()
        play_world = play_engine.data_model.get_service(World)
        play_door = play_world.find_first("Door")

        self.assertIsInstance(play_door, Door)
        self.assertTrue(play_door.locked)
        self.assertNotEqual(play_door.object_id, door.object_id)
        self.assertEqual(play_door.extensions["source_object_id"], door.object_id)
        self.assertIsNone(
            play_engine.data_model.find_first("Editor", recursive=False)
        )

    def test_property_change_signal_observes_live_edits(self) -> None:
        door = Door(object_id="door", name="Door")
        changes = []
        door.property_changed.connect(
            lambda obj, name, old, new: changes.append((obj.object_id, name, old, new))
        )
        door.locked = True
        self.assertEqual(changes, [("door", "locked", False, True)])


if __name__ == "__main__":
    unittest.main()
