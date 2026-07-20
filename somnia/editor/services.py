"""Editor-only services implemented as ordinary Somnia objects."""

from __future__ import annotations

from somnia.model import Property, Service, register_object_class


@register_object_class("somnia.editor.EditorService")
class EditorService(Service):
    """Root of editor-only state inside the editor's DataModel."""

    def __init__(self, object_id=None, name=None):
        super().__init__(object_id=object_id, name=name or "Editor")

    def get_service(self, service_type):
        for child in self.children:
            if isinstance(child, service_type):
                return child
        return None

    def ensure_service(self, service_type, name=None):
        existing = self.get_service(service_type)
        if existing is not None:
            return existing
        service = service_type(name=name)
        self.add_child(service)
        return service


@register_object_class("somnia.editor.SelectionService")
class SelectionService(Service):
    selected_object_ids = Property(
        [],
        value_type=list,
        serializable=False,
        category="Editor",
    )

    def __init__(self, object_id=None, name=None):
        super().__init__(object_id=object_id, name=name or "Selection")

    def select(self, objects, additive=False):
        selected = list(self.selected_object_ids) if additive else []
        for obj in objects:
            if obj.object_id not in selected:
                selected.append(obj.object_id)
        self.selected_object_ids = selected

    def set_one(self, obj):
        self.selected_object_ids = [obj.object_id]

    def clear(self):
        self.selected_object_ids = []

    def resolve(self, data_model):
        by_id = {obj.object_id: obj for obj in data_model.walk(include_self=True)}
        return [
            by_id[object_id]
            for object_id in self.selected_object_ids
            if object_id in by_id
        ]


@register_object_class("somnia.editor.HistoryService")
class HistoryService(Service):
    undo_count = Property(
        0,
        value_type=int,
        serializable=False,
        category="Editor",
        read_only=True,
    )
    redo_count = Property(
        0,
        value_type=int,
        serializable=False,
        category="Editor",
        read_only=True,
    )

    def __init__(self, object_id=None, name=None):
        super().__init__(object_id=object_id, name=name or "History")
        self._undo_stack = []
        self._redo_stack = []

    def _refresh_counts(self):
        self._loading = True
        self.undo_count = len(self._undo_stack)
        self.redo_count = len(self._redo_stack)
        self._loading = False

    def execute(self, command):
        command.execute()
        self._undo_stack.append(command)
        self._redo_stack = []
        self._refresh_counts()
        return command

    def undo(self):
        if not self._undo_stack:
            return None
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)
        self._refresh_counts()
        return command

    def redo(self):
        if not self._redo_stack:
            return None
        command = self._redo_stack.pop()
        command.execute()
        self._undo_stack.append(command)
        self._refresh_counts()
        return command

    def clear(self):
        self._undo_stack = []
        self._redo_stack = []
        self._refresh_counts()


def install_editor_services(data_model):
    """Install the editor branch into an editor DataModel."""
    editor = data_model.ensure_service(EditorService)
    editor.ensure_service(SelectionService)
    editor.ensure_service(HistoryService)
    return editor
