# SEM and SEMJ model formats

Somnia Engine models use one logical schema with two encodings.

- `.semj`: literal UTF-8 JSON for editing, source control, inspection, and interchange.
- `.sem`: a compact binary encoding for builds and fast loading.

Neither format is an archive and `.semj` is never base64-encoded or wrapped in another container.

## Shared logical document

Every model document contains:

- `format`: `somnia-model`
- `version`: positive integer schema version
- `name`: model name
- `root_ids`: ordered list of top-level object IDs
- `objects`: ordered object records
- `metadata`: format-level extension data

Each object record contains:

- `id`: stable string ID
- `type`: registered Somnia object type
- `name`: display name
- `parent`: parent object ID or `null`
- `properties`: reflected serializable properties
- `tags`: ordered tags
- `extensions`: unknown or plugin-specific data

Child order is derived from object-record order among objects with the same parent.

## SEMJ example

```json
{
  "format": "somnia-model",
  "version": 1,
  "name": "Chair",
  "root_ids": ["root"],
  "objects": [
    {
      "id": "root",
      "type": "somnia.ModelNode",
      "name": "Chair",
      "parent": null,
      "properties": {
        "transform": {
          "position": [0.0, 0.0, 0.0],
          "rotation": [0.0, 0.0, 0.0, 1.0],
          "scale": [1.0, 1.0, 1.0]
        }
      },
      "tags": [],
      "extensions": {}
    }
  ],
  "metadata": {}
}
```

## Initial SEM binary layout

All integer fields are little-endian.

```text
8 bytes   magic: SOMNIA\0\1
u32       schema version
u32       UTF-8 JSON payload length
N bytes   canonical UTF-8 JSON payload
```

Version 1 intentionally wraps the exact logical JSON payload in a validated binary envelope. This establishes stable extensions, round-trip behavior, and tooling before introducing string tables and packed property records. Later SEM container versions may optimize storage while preserving the same logical model schema.

## Compatibility rules

- Loaders reject invalid magic and unsupported required versions.
- Unknown object types are preserved as `UnknownModelNode`.
- Unknown properties and extension values are retained.
- Saving an unmodified unknown object must not discard its data.
- Conversion between `.semj` and `.sem` must preserve the logical document.
