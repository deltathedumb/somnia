"""Editor operations presented as views and commands over the live DataModel."""

from __future__ import annotations

from somnia.model import OBJECT_TYPES

from .commands import (
    CreateObjectCommand,
    DeleteObjectCommand,
    ReparentCommand,
    SetPropertyCommand,
)
from .services import HistoryService, SelectionService, install_editor_services


class EditorSession:
    """Non-visual editor controller; UI panels bind directly to this model."""

    def __init__(self, engine):
        self.engine = engine
        self.data_model = engine.data_model
        self.editor_service = install_editor_services(self.data_model)
        self.selection = self.editor_service.get_service(SelectionService)
        self.history = self.editor_service.get_service(HistoryService)

    def scene_tree(self):
        return list(self.data_model.walk(include_self=True))

    def create_object(self, type_name, parent, name=None, index=None):
        obj = OBJECT_TYPES.create(type_name, name=name)
        self.history.execute(CreateObjectCommand(parent, obj, index=index))
        self.selection.set_one(obj)
        return obj

    def delete_object(self, obj):
        self.history.execute(DeleteObjectCommand(obj))
        self.selection.clear()

    def reparent_object(self, obj, new_parent, index=None):
        self.history.execute(ReparentCommand(obj, new_parent, new_index=index))

    def set_property(self, obj, property_name, value):
        self.history.execute(SetPropertyCommand(obj, property_name, value))

    def inspect_object(self, obj):
        rows = []
        for name, descriptor in obj.reflected_properties().items():
            if not descriptor.editor_visible:
                continue
            row = descriptor.describe()
            row["value"] = getattr(obj, name)
            rows.append(row)
        return rows

    def registered_object_classes(self):
        return OBJECT_TYPES.describe()

    def play(self):
        return self.engine.clone_for_play()
