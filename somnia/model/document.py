"""Serializable documents containing ordinary Somnia objects."""

from __future__ import annotations

from .core import SomniaObject


class ModelDocument:
    """A named set of top-level Somnia objects.

    The document is only a file boundary. Its contents are the same objects used
    by the editor and runtime; there is no alternate serialized scene class.
    """

    def __init__(self, name="Model", roots=None, metadata=None):
        self.name = str(name)
        self.roots = list(roots or [])
        self.metadata = dict(metadata or {})

    def add_root(self, root):
        if not isinstance(root, SomniaObject):
            raise TypeError("model roots must be SomniaObject instances")
        if root.parent is not None:
            raise ValueError("a model root cannot already have a parent")
        if root not in self.roots:
            self.roots.append(root)
        return root

    def remove_root(self, root):
        self.roots.remove(root)
        return root

    def walk(self):
        for root in self.roots:
            yield from root.walk(include_self=True)

    def by_id(self):
        objects = {}
        for obj in self.walk():
            if obj.object_id in objects:
                raise ValueError("duplicate Somnia object ID: " + obj.object_id)
            objects[obj.object_id] = obj
        return objects

    def find(self, object_id):
        return self.by_id().get(object_id)

    def validate(self):
        objects = self.by_id()
        root_ids = set(root.object_id for root in self.roots)
        for root in self.roots:
            if root.parent is not None:
                raise ValueError("root object has a parent: " + root.object_id)
        for obj in objects.values():
            if obj.parent is None and obj.object_id not in root_ids:
                raise ValueError("detached object is not a document root: " + obj.object_id)
            if obj.parent is not None and obj.parent.object_id not in objects:
                raise ValueError("object parent is outside the document: " + obj.object_id)
        return True

    def clone(self):
        return ModelDocument(
            name=self.name,
            roots=[root.clone() for root in self.roots],
            metadata=dict(self.metadata),
        )

    def __repr__(self):
        return "ModelDocument(name=" + repr(self.name) + ", roots=" + repr(len(self.roots)) + ")"
