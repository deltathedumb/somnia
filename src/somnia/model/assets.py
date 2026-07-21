"""Serializable asset records shared by the editor, builds, and runtimes."""

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
    """One source asset known to Somnia's project asset database."""

    asset_id = Property("", value_type=str, category="Asset", read_only=True)
    source_path = Property("", value_type=str, category="Asset")
    kind = Property(AssetKind.UNKNOWN, value_type=str, category="Asset")
    content_hash = Property("", value_type=str, category="Import", read_only=True)
    size_bytes = Property(0, value_type=int, category="Import", minimum=0, read_only=True)
    modified_ns = Property(0, value_type=int, category="Import", minimum=0, read_only=True)
    importer = Property("builtin", value_type=str, category="Import")
    imported_path = Property("", value_type=str, category="Import")
    metadata = Property({}, value_type=dict, category="Asset")

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
            self.asset_id = str(asset_id)
            self.source_path = str(source_path)
            self.kind = AssetKind.normalize(kind)
            self.content_hash = str(content_hash)
            self.size_bytes = int(size_bytes)
            self.modified_ns = int(modified_ns)
        finally:
            self._loading = False
        return self
