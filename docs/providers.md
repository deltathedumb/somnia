# Providers

Providers are Somnia's equivalent of Roblox services: user-facing singleton objects directly beneath the `Game` DataModel. A provider exposes a stable game API; replaceable low-level implementations are called **backends**.

## Canonical Explorer hierarchy

```text
Game
├── Scene
├── Environment
├── ServerScriptProvider
├── ServerStorage
├── SharedStorage
├── ClientStorage
├── PlayerProvider
├── PlayerScriptProvider
├── PlayerUIProvider
├── Assets
├── PhysicsProvider       [hidden]
├── NetworkProvider       [hidden]
├── HttpProvider          [hidden]
├── AnimationProvider     [hidden]
├── AudioProvider         [hidden]
├── InputProvider         [hidden]
├── TimeProvider          [hidden]
├── NavigationProvider    [hidden]
└── LocalizationProvider  [hidden]
```

Hidden providers are omitted from the default Explorer view, not removed from the DataModel. The editor can reveal them through **Show Hidden Providers**.

```python
physics = game.get_provider(PhysicsProvider)
network = game.get_provider("NetworkProvider")
scene = game.get_provider("Workspace")  # compatibility alias for Scene
```

## Provider realms

| Provider | Server | Client | Hidden |
|---|---:|---:|---:|
| Scene | Yes | Yes | No |
| Environment | Yes | Yes | No |
| PhysicsProvider | Yes | Yes | Yes |
| ServerScriptProvider | Yes | No | No |
| ServerStorage | Yes | No | No |
| SharedStorage | Yes | Yes | No |
| ClientStorage | No | Yes | No |
| PlayerProvider | Yes | Yes | No |
| PlayerScriptProvider | No | Yes | No |
| PlayerUIProvider | No | Yes | No |
| NetworkProvider | Yes | Yes | Yes |
| HttpProvider | Yes | Yes | Yes |
| AnimationProvider | Yes | Yes | Yes |
| AudioProvider | No | Yes | Yes |
| InputProvider | No | Yes | Yes |
| TimeProvider | Yes | Yes | Yes |
| Assets | Yes | Yes | No |
| NavigationProvider | Yes | No | Yes |
| LocalizationProvider | No | Yes | Yes |

The project/editor realm contains every provider so the complete game can be authored in one hierarchy. Exporting clones and filters that hierarchy into independent server and client DataModels.

## Rules

- Each canonical provider is a singleton.
- Providers are direct children of `Game` and cannot be reparented beneath ordinary objects.
- Canonical providers cannot be deleted through the editor.
- Provider IDs are stable, such as `provider:Scene` and `provider:PhysicsProvider`.
- Visible and hidden providers use the same reflection and SEM/SEMJ serialization systems as every other Somnia object.
- Objects placed under a realm-specific provider inherit that packaging boundary. Anything under `ServerStorage` is absent from client exports.
