# Export types

Somnia projects are authored beneath three fixed roots: `Server`, `Shared`, and `Client`. Exporting clones complete roots into independent runtime DataModels.

## Root partition

```text
Authored Game
├── Server
├── Shared
└── Client

Server runtime          Client runtime
├── Server              ├── Shared
└── Shared              └── Client
```

`Shared` is cloned separately into each runtime. Server and client never share mutable object instances merely because content was authored beneath the same root.

## Client

`Client` is the normal complete game export. It contains two independent runtime packages:

```text
Client executable
├── invisible integrated server Game
│   ├── Server
│   └── Shared
└── client Game
    ├── Shared
    └── Client
```

The two runtimes communicate through their separate `Shared.NetworkProvider` objects. The default integrated-server path creates paired `LocalTransportEndpoint` objects:

```text
Server game.shared.NetworkProvider
                 ↕ LocalTransport packets
Client game.shared.NetworkProvider
```

```python
client = editor.play()
server = client.integrated_server

client_network = client.data_model.shared.NetworkProvider
server_network = server.data_model.shared.NetworkProvider

client_network.send("JoinRequest", {"name": "Player"})
request = server_network.receive()[0]
```

`Client` is the default for standalone single-player games and can later support listen-server multiplayer.

## DedicatedServer

`DedicatedServer` contains only the authoritative server package:

```text
Game
├── Server
│   ├── PhysicsProvider
│   ├── ServerScriptProvider
│   ├── ServerStorage
│   ├── NavigationProvider
│   └── Assets
└── Shared
    ├── Scene
    ├── SharedStorage
    ├── PlayerProvider
    ├── NetworkProvider
    ├── HttpProvider
    ├── AnimationProvider
    ├── TimeProvider
    └── Assets
```

It has no `Client` root, so client storage, UI, player scripts, input, audio, localization, visual environment data, and client assets cannot leak into the package.

## DedicatedClient

`DedicatedClient` contains only:

```text
Game
├── Shared
└── Client
```

It never embeds the `Server` root. Server scripts, server storage, authoritative physics configuration, navigation data, and server assets are therefore absent from the generated DataModel.

Its `NetworkProvider` must be attached to a remote transport by the exported runtime rather than silently creating a local server.

## API

```python
from somnia import Engine, ExportType

engine = Engine()

client_plan = engine.create_export_plan(ExportType.CLIENT)
server_plan = engine.create_export_plan(ExportType.DEDICATED_SERVER)
proprietary_client_plan = engine.create_export_plan(
    ExportType.DEDICATED_CLIENT
)
```

Each plan contains one or two `RuntimePackage` objects with independently cloned Games.

```python
client_package = proprietary_client_plan.package_for("client")
print(client_package.root_names())
# ["Shared", "Client"]

print(client_package.provider_paths())
# ["Shared.Scene", ..., "Client.InputProvider", ...]
```

## Security boundary

The root partition is a packaging boundary, not merely an execution flag. A DedicatedClient's Game does not contain the `Server` root or any descendant. Secrets, private scripts, authoritative native libraries, and proprietary logic must be placed beneath `Server` so they never enter client output.
