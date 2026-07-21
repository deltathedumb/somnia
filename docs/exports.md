# Export types

Somnia projects are authored beneath three fixed roots: `Server`, `Shared`, and `Client`. Each export option selects an exact root combination.

## Export matrix

| Export | Included roots | Runtime package |
|---|---|---|
| `Client` | `Shared + Client` | Client |
| `DedicatedClient` | `Client` | Client |
| `DedicatedServer` | `Server + Shared` | Server |

Exported roots are cloned into an independent `Game`. No export silently adds a missing root during runtime initialization.

## Client

`Client` is the normal client export:

```text
Game
├── Shared
└── Client
```

It contains shared world data and systems alongside client-specific UI, input, audio, scripts, storage, environment data, localization, and assets. It does not contain the `Server` root and does not embed an integrated server.

Typical provider access remains hierarchical:

```python
scene = game.shared.Scene
network = game.shared.NetworkProvider
inputs = game.client.InputProvider
```

## DedicatedClient

`DedicatedClient` contains only:

```text
Game
└── Client
```

It excludes both `Server` and `Shared`, including `Shared.Scene`, `SharedStorage`, `NetworkProvider`, shared scripts/content, and shared assets. Runtime initialization preserves this exact root set.

## DedicatedServer

`DedicatedServer` contains:

```text
Game
├── Server
└── Shared
```

This includes authoritative server systems together with shared world data and systems. It excludes the entire `Client` root, including client storage, UI, player scripts, input, audio, localization, environment data, and client assets.

## API

```python
from somnia import Engine, ExportType

engine = Engine()

client = engine.create_export_plan(ExportType.CLIENT)
dedicated_client = engine.create_export_plan(ExportType.DEDICATED_CLIENT)
dedicated_server = engine.create_export_plan(ExportType.DEDICATED_SERVER)

print(client.package_for("client").root_names())
# ["Shared", "Client"]

print(dedicated_client.package_for("client").root_names())
# ["Client"]

print(dedicated_server.package_for("server").root_names())
# ["Server", "Shared"]
```

Every plan contains exactly one `RuntimePackage`.

## Security boundary

The root partition is a packaging boundary, not merely an execution flag. Client exports cannot contain descendants of `Server`, and `DedicatedClient` additionally cannot contain descendants of `Shared`. Secrets, private scripts, authoritative native libraries, and proprietary logic must remain beneath `Server`.
