# Export types

Somnia projects are always logically split into server and client runtimes. Exporting partitions the same authored `Game` hierarchy according to provider realm metadata.

## Client

`Client` is the normal complete game export. It contains two independent runtime packages:

```text
Client executable
├── invisible integrated server DataModel
└── client DataModel
```

The two runtimes communicate through their separate `NetworkProvider` objects. The default integrated-server path creates paired `LocalTransportEndpoint` objects:

```text
Server NetworkProvider
        ↕ LocalTransport packets
Client NetworkProvider
```

This is an in-memory transport, but it preserves the same explicit packet boundary expected from future remote transports. The client and server never share authoritative object instances merely because they are in one executable.

```python
client = editor.play()
server = client.integrated_server

client_network = client.get_provider(NetworkProvider)
server_network = server.get_provider(NetworkProvider)

client_network.send("JoinRequest", {"name": "Player"})
request = server_network.receive()[0]
```

`Client` is the default for standalone single-player games and can later support listen-server multiplayer.

## DedicatedServer

`DedicatedServer` contains only the authoritative server package. It omits rendering, input, player UI, client storage, and player scripts.

Typical included providers:

```text
Scene
Environment
PhysicsProvider
ServerScriptProvider
ServerStorage
SharedStorage
PlayerProvider
NetworkProvider
HttpProvider
AnimationProvider
TimeProvider
Assets
NavigationProvider
```

## DedicatedClient

`DedicatedClient` contains only the client package and never embeds server code. It is intended for games whose authoritative servers are proprietary or separately hosted.

The build system enforces these exclusions:

```text
ServerScriptProvider  excluded
ServerStorage         excluded
integrated server     absent
```

A DedicatedClient may contain `ClientStorage`, `PlayerScriptProvider`, `PlayerUIProvider`, rendering assets, input, audio, localization, and client-safe shared content. Its `NetworkProvider` must be attached to a remote transport by the exported game runtime rather than silently creating a local server.

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

Each plan contains one or two `RuntimePackage` objects with independently cloned DataModels.

```python
client_package = proprietary_client_plan.package_for("client")
print(client_package.provider_names())
```

## Security boundary

The export partition is a packaging boundary, not merely an execution flag. A DedicatedClient's cloned DataModel does not contain server-only providers or their descendants. Server secrets, private scripts, and proprietary authority logic must be placed under server-only providers so they never enter client output.
