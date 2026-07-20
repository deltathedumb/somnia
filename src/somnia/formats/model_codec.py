"""SEM/SEMJ serialization for Somnia's unified object hierarchy."""

from __future__ import annotations

import json
import struct
from pathlib import Path

from somnia.model.core import OBJECT_TYPES, UnknownObject
from somnia.model.document import ModelDocument


FORMAT_NAME = "somnia-model"
SCHEMA_VERSION = 1
SEM_MAGIC = b"SOMNIA\x00\x01"
_HEADER = struct.Struct("<II")


class ModelFormatError(ValueError):
    pass


def _record_for_object(obj):
    return {
        "id": obj.object_id,
        "type": obj.type_name,
        "name": obj.name,
        "parent": obj.parent.object_id if obj.parent is not None else None,
        "properties": obj.serializable_properties(),
        "tags": list(obj.tags),
        "extensions": dict(obj.extensions),
    }


def document_to_data(document):
    document.validate()
    return {
        "format": FORMAT_NAME,
        "version": SCHEMA_VERSION,
        "name": document.name,
        "root_ids": [root.object_id for root in document.roots],
        "objects": [_record_for_object(obj) for obj in document.walk()],
        "metadata": dict(document.metadata),
    }


def _require(condition, message):
    if not condition:
        raise ModelFormatError(message)


def data_to_document(data, registry=OBJECT_TYPES):
    _require(isinstance(data, dict), "model document must be a JSON object")
    _require(data.get("format") == FORMAT_NAME, "not a Somnia model document")
    _require(data.get("version") == SCHEMA_VERSION, "unsupported Somnia model schema")

    records = data.get("objects")
    root_ids = data.get("root_ids")
    _require(isinstance(records, list), "model objects must be an array")
    _require(isinstance(root_ids, list), "model root_ids must be an array")

    objects = {}
    record_order = []
    for record in records:
        _require(isinstance(record, dict), "object record must be a JSON object")
        object_id = record.get("id")
        type_name = record.get("type")
        name = record.get("name")
        _require(isinstance(object_id, str) and object_id, "object ID must be non-empty")
        _require(isinstance(type_name, str) and type_name, "object type must be non-empty")
        _require(object_id not in objects, "duplicate object ID: " + object_id)
        obj = registry.create(type_name, object_id=object_id, name=name)
        if isinstance(obj, UnknownObject):
            obj.original_type = type_name
        tags = record.get("tags", [])
        extensions = record.get("extensions", {})
        properties = record.get("properties", {})
        _require(isinstance(tags, list), "object tags must be an array")
        _require(isinstance(extensions, dict), "object extensions must be an object")
        _require(isinstance(properties, dict), "object properties must be an object")
        obj.tags = list(tags)
        obj.extensions = dict(extensions)
        obj.apply_serialized_properties(properties)
        objects[object_id] = obj
        record_order.append((obj, record.get("parent")))

    for obj, parent_id in record_order:
        if parent_id is None:
            continue
        _require(isinstance(parent_id, str), "parent ID must be a string or null")
        parent = objects.get(parent_id)
        _require(parent is not None, "missing parent object: " + parent_id)
        try:
            parent.add_child(obj)
        except ValueError as error:
            raise ModelFormatError(str(error)) from error

    roots = []
    seen_roots = set()
    for root_id in root_ids:
        _require(isinstance(root_id, str), "root ID must be a string")
        root = objects.get(root_id)
        _require(root is not None, "missing root object: " + root_id)
        _require(root.parent is None, "listed root has a parent: " + root_id)
        _require(root_id not in seen_roots, "duplicate root ID: " + root_id)
        seen_roots.add(root_id)
        roots.append(root)

    for obj in objects.values():
        if obj.parent is None:
            _require(obj.object_id in seen_roots, "unlisted root object: " + obj.object_id)

    metadata = data.get("metadata", {})
    _require(isinstance(metadata, dict), "model metadata must be an object")
    document = ModelDocument(
        name=data.get("name", "Model"),
        roots=roots,
        metadata=metadata,
    )
    document.validate()
    return document


def dumps_semj(document, *, indent=2):
    return json.dumps(
        document_to_data(document),
        ensure_ascii=False,
        indent=indent,
        sort_keys=False,
    ) + "\n"


def loads_semj(text, registry=OBJECT_TYPES):
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise ModelFormatError("invalid SEMJ JSON: " + str(error)) from error
    return data_to_document(data, registry=registry)


def dumps_sem(document):
    payload = json.dumps(
        document_to_data(document),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return SEM_MAGIC + _HEADER.pack(SCHEMA_VERSION, len(payload)) + payload


def loads_sem(data, registry=OBJECT_TYPES):
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("SEM data must be bytes")
    raw = bytes(data)
    minimum = len(SEM_MAGIC) + _HEADER.size
    _require(len(raw) >= minimum, "SEM file is truncated")
    _require(raw[: len(SEM_MAGIC)] == SEM_MAGIC, "invalid SEM magic")
    schema_version, payload_length = _HEADER.unpack_from(raw, len(SEM_MAGIC))
    _require(schema_version == SCHEMA_VERSION, "unsupported SEM schema version")
    payload_start = minimum
    payload_end = payload_start + payload_length
    _require(payload_end == len(raw), "SEM payload length does not match file size")
    try:
        data_object = json.loads(raw[payload_start:payload_end].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ModelFormatError("invalid SEM payload: " + str(error)) from error
    return data_to_document(data_object, registry=registry)


def save_model(document, path):
    destination = Path(path)
    suffix = destination.suffix.lower()
    if suffix == ".semj":
        destination.write_text(dumps_semj(document), encoding="utf-8")
    elif suffix == ".sem":
        destination.write_bytes(dumps_sem(document))
    else:
        raise ModelFormatError("model path must end in .sem or .semj")
    return destination


def load_model(path, registry=OBJECT_TYPES):
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix == ".semj":
        return loads_semj(source.read_text(encoding="utf-8"), registry=registry)
    if suffix == ".sem":
        return loads_sem(source.read_bytes(), registry=registry)
    raise ModelFormatError("model path must end in .sem or .semj")
