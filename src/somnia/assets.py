"""Deterministic realm-specific source-asset discovery and indexing."""

from __future__ import annotations

import hashlib
from pathlib import Path

from somnia.model.assets import Asset, AssetKind
from somnia.model.provider import RealmKey
from somnia.model.providers import Assets, get_provider


_KIND_BY_SUFFIX = {
    ".obj": AssetKind.MESH,
    ".gltf": AssetKind.MESH,
    ".glb": AssetKind.MESH,
    ".fbx": AssetKind.MESH,
    ".png": AssetKind.TEXTURE,
    ".jpg": AssetKind.TEXTURE,
    ".jpeg": AssetKind.TEXTURE,
    ".bmp": AssetKind.TEXTURE,
    ".tga": AssetKind.TEXTURE,
    ".wav": AssetKind.AUDIO,
    ".ogg": AssetKind.AUDIO,
    ".mp3": AssetKind.AUDIO,
    ".flac": AssetKind.AUDIO,
    ".py": AssetKind.SCRIPT,
    ".sem": AssetKind.MODEL,
    ".semj": AssetKind.MODEL,
    ".rbxm": AssetKind.MODEL,
    ".rbxmx": AssetKind.MODEL,
    ".json": AssetKind.DATA,
    ".toml": AssetKind.DATA,
    ".yaml": AssetKind.DATA,
    ".yml": AssetKind.DATA,
    ".ttf": AssetKind.FONT,
    ".otf": AssetKind.FONT,
}


def normalize_asset_path(value):
    path = str(value).replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    if path.startswith("/") or path == ".." or path.startswith("../"):
        raise ValueError("asset paths must be relative to the Assets root")
    parts = [part for part in path.split("/") if part not in ("", ".")]
    if ".." in parts:
        raise ValueError("asset paths cannot leave the Assets root")
    return "/".join(parts)


def asset_id_for_path(relative_path, realm=None):
    normalized = normalize_asset_path(relative_path)
    identity = normalized
    if realm is not None:
        identity = RealmKey.normalize(realm) + ":" + normalized
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return digest[:24]


def infer_asset_kind(relative_path):
    suffix = Path(str(relative_path)).suffix.lower()
    return _KIND_BY_SUFFIX.get(suffix, AssetKind.UNKNOWN)


def hash_file(path, chunk_size=1024 * 1024):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


class AssetRefreshResult:
    def __init__(self):
        self.added = []
        self.updated = []
        self.removed = []
        self.unchanged = []

    @property
    def changed(self):
        return bool(self.added or self.updated or self.removed)

    def to_dict(self):
        return {
            "added": list(self.added),
            "updated": list(self.updated),
            "removed": list(self.removed),
            "unchanged": list(self.unchanged),
        }


class AssetDatabase:
    """Synchronize one realm's :class:`Assets` provider with files on disk."""

    def __init__(self, provider, project_root="."):
        if not isinstance(provider, Assets):
            raise TypeError("AssetDatabase requires a somnia.Assets provider")
        if provider.realm_root is None:
            raise ValueError("Assets must be attached beneath Server, Shared, or Client")
        self.provider = provider
        self.project_root = Path(project_root).resolve()

    @classmethod
    def from_data_model(cls, data_model, project_root=".", realm=RealmKey.SHARED):
        return cls(
            get_provider(data_model, Assets, realm=realm),
            project_root=project_root,
        )

    @property
    def realm_key(self):
        return self.provider.realm_root.realm_key

    @property
    def source_root(self):
        return (self.project_root / self.provider.root_path).resolve()

    def source_path(self, relative_path):
        normalized = normalize_asset_path(relative_path)
        candidate = (self.source_root / normalized).resolve()
        try:
            candidate.relative_to(self.source_root)
        except ValueError as error:
            raise ValueError("asset path leaves the configured Assets root") from error
        return candidate

    def discover(self):
        root = self.source_root
        if not root.exists():
            return []
        files = []
        for path in root.rglob("*"):
            if path.is_file():
                files.append(path)
        files.sort(key=lambda path: path.relative_to(root).as_posix())
        return files

    def refresh(self, remove_missing=True):
        result = AssetRefreshResult()
        existing = {asset.source_path: asset for asset in self.provider.asset_records()}
        seen = set()

        for discovered_path in self.discover():
            relative_path = normalize_asset_path(
                discovered_path.relative_to(self.source_root).as_posix()
            )
            path = self.source_path(relative_path)
            seen.add(relative_path)
            asset_id = asset_id_for_path(relative_path, realm=self.realm_key)
            content_hash = hash_file(path)
            stat = path.stat()
            kind = infer_asset_kind(relative_path)
            asset = existing.get(relative_path)

            if asset is None:
                asset = Asset(
                    object_id="asset:" + self.realm_key + ":" + asset_id,
                    name=Path(relative_path).name,
                )
                self.provider.add_child(asset)
                result.added.append(asset_id)
            else:
                changed = (
                    asset.asset_id != asset_id
                    or asset.content_hash != content_hash
                    or asset.size_bytes != stat.st_size
                    or asset.modified_ns != stat.st_mtime_ns
                    or asset.kind != kind
                )
                if changed:
                    result.updated.append(asset_id)
                else:
                    result.unchanged.append(asset_id)

            asset.update_source(
                asset_id=asset_id,
                source_path=relative_path,
                kind=kind,
                content_hash=content_hash,
                size_bytes=stat.st_size,
                modified_ns=stat.st_mtime_ns,
            )

        if remove_missing:
            for relative_path in sorted(existing):
                if relative_path in seen:
                    continue
                asset = existing[relative_path]
                result.removed.append(asset.asset_id)
                self.provider.remove_child(asset)

        return result
