"""Serializable immutable asset records shared by editor, builds, and runtimes."""

from __future__ import annotations

from .core import Property, SomniaObject, register_object_class


class AssetKind:
    UNKNOWN = "unknown"
    MESH = "mesh"
    TEXTURE = "texture"
    AUDIO = "audio"
    SCRIPT = "script"
    MODEL = "model"
    DATA = "data"
    FONT = "font"

    @classmethod
    def normalize(cls, value):
        normalized = str(value or cls.UNKNOWN).lower()
        supported = (
            cls.UNKNOWN,
            cls.MESH,
            cls.TEXTURE,
            cls.AUDIO,
            cls.SCRIPT,
            cls.MODEL,
            cls.DATA,
            cls.FONT,
        )
        if normalized not in supported:
            raise ValueError("unsupported Somnia asset kind: " + normalized)
        return normalized


@register_object_class("somnia.Asset")
class Asset(SomniaObject):
    """One externally immutable imported asset database record.

    The asset database may refresh a record through its internal update methods,
    while project scripts and editor property edits cannot mutate imported data.
    Mutable runtime instances reference these records rather than modifying them.
    """

    name = Property("Asset", value_type=str, category="Identity", read_only=True)
    asset_id = Property("", value_type=str, category="Asset", read_only=True)
    source_path = Property("", value_type=str, category="Asset", read_only=True)
    kind = Property(AssetKind.UNKNOWN, value_type=str, category="Asset", read_only=True)
    content_hash = Property("", value_type=str, category="Import", read_only=True)
    size_bytes = Property(0, value_type=int, category="Import", minimum=0, read_only=True)
    modified_ns = Property(0, value_type=int, category="Import", minimum=0, read_only=True)
    importer = Property("builtin", value_type=str, category="Import", read_only=True)
    imported_path = Property("", value_type=str, category="Import", read_only=True)
    metadata = Property({}, value_type=dict, category="Asset", read_only=True)

    def update_source(
        self,
        *,
        asset_id,
        source_path,
        kind,
        content_hash,
        size_bytes,
        modified_ns,
    ):
        self._loading = True
        try:
            self.name = str(source_path).replace("\\", "/").rsplit("/", 1)[-1]
            self.asset_id = str(asset_id)
            self.source_path = str(source_path)
            self.kind = AssetKind.normalize(kind)
            self.content_hash = str(content_hash)
            self.size_bytes = int(size_bytes)
            self.modified_ns = int(modified_ns)
        finally:
            self._loading = False
        return self

    def update_import(self, *, importer="builtin", imported_path="", metadata=None):
        self._loading = True
        try:
            self.importer = str(importer)
            self.imported_path = str(imported_path)
            self.metadata = dict(metadata or {})
        finally:
            self._loading = False
        return self
