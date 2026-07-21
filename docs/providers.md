# Providers

Somnia providers are user-facing singleton systems grouped beneath three fixed realm roots. Replaceable low-level implementations are called **backends**.

`Server`, `Shared`, and `Client` are the only direct children of `Game`. They cannot be renamed, deleted, duplicated, disabled, or reparented.

## Canonical Explorer hierarchy

```text
Game
├── Server
│   ├── PhysicsProvider       [hidden]
│   ├── ServerScriptProvider
│   ├── ServerStorage
│   ├── NavigationProvider    [hidden]
│   └── Assets
├── Shared
│   ├── Scene
│   ├── SharedStorage
│   ├── PlayerProvider
│   ├── NetworkProvider       [hidden]
│   ├── HttpProvider          [hidden]
│   ├── AnimationProvider     [hidden]
│   ├── TimeProvider          [hidden]
│   └── Assets
└── Client
    ├── Environment
    ├── ClientStorage
    ├── PlayerScriptProvider
    ├── PlayerUIProvider
    ├── AudioProvider         [hidden]
    ├── InputProvider         [hidden]
    ├── LocalizationProvider  [hidden]
    └── Assets
```

Hidden providers are omitted from the default Explorer view, not removed from the hierarchy. The editor can reveal them through **Show Hidden Providers**.

## Scripting API

Realm-root access is the normal scripting style:

```python
server = game.server
physics_provider = server.PhysicsProvider
server_storage = server.ServerStorage

shared = game.shared
scene = shared.Scene
network = shared.NetworkProvider

client = game.client
input_provider = client.InputProvider
```

Provider names are exact-case attributes on their realm root. `game.server`, `game.shared`, and `game.client` use lowercase root accessors.

Global lookup remains available for tooling and engine code when a provider is unambiguous:

```python
physics = game.get_provider(PhysicsProvider)
scene = game.get_provider("Workspace")  # compatibility alias for Scene
```

Because every realm contains an `Assets` provider, asset lookup must specify the realm:

```python
server_assets = game.get_provider(Assets, realm="server")
shared_assets = game.shared.Assets
client_assets = game.client.Assets
```

## Packaging boundaries

| Root | Included in server | Included in client |
|---|---:|---:|
| Server | Yes | No |
| Shared | Yes | Yes |
| Client | No | Yes |

The authored project and editor contain all three roots. Runtime exports clone complete roots instead of filtering a flat list of providers.

- Server package: `Server + Shared`
- Client package: `Shared + Client`
- Editor/project: `Server + Shared + Client`

`Shared` is cloned independently into each runtime. It does not mean that server and client share live object instances.

## Assets

Each root owns a separate immutable `Assets` provider:

```text
Server/Assets  -> assets/server
Shared/Assets  -> assets/shared
Client/Assets  -> assets/client
```

Imported `Asset` records are externally read-only. The asset database may internally refresh hashes and import results when source files change; mutable runtime objects reference those records instead of modifying them.

The same relative file path receives a different asset ID in each realm, preventing accidental collisions between server-only, shared, and client-only content.

## Rules

- `Server`, `Shared`, and `Client` are the only top-level `Game` objects.
- Each provider is a singleton within its assigned root.
- Providers cannot be moved between roots.
- Canonical providers and realm roots cannot be deleted through the editor.
- Provider IDs include their root, such as `provider:server:PhysicsProvider`.
- Legacy flat projects are migrated by routing old top-level providers into their canonical root.
- Objects beneath a root inherit its packaging boundary.
