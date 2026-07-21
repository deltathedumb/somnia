# Input frames and asset database

Somnia keeps input collection and asset discovery separate from rendering. A renderer may use raylib, another native backend, or a headless test implementation without changing the runtime-facing contracts.

## Deterministic input frames

Every client engine frame polls one `InputBackend`. The backend returns an `InputFrame` containing:

- an ordered list of transitions,
- the complete set of held buttons,
- named axis values,
- the current pointer position,
- per-frame wheel movement,
- per-frame text input.

`Engine.input_frame` retains the most recent frame. `game.client.InputProvider` mirrors its state and emits `input_began`, `input_changed`, `input_ended`, and `frame_updated` signals.

```python
from somnia import Engine, Game, RuntimeRealm
from somnia.input import InputEvent, InputEventType, QueueInputBackend

backend = QueueInputBackend()
backend.submit(
    events=[InputEvent(InputEventType.BUTTON_DOWN, code="KeyW")]
)

engine = Engine(
    Game(realm=RuntimeRealm.CLIENT),
    realm=RuntimeRealm.CLIENT,
    input_backend=backend,
)
engine.frame()

inputs = engine.data_model.client.InputProvider
assert inputs.is_down("KeyW")
```

`NullInputBackend` produces empty frames. `QueueInputBackend` is intended for tests, editor injection, deterministic replays, and compiler parity probes. Native window backends can implement the same `InputBackend` interface later. Rich input helpers are imported explicitly from `somnia.input` so unrelated `import somnia` builds retain the smallest compiler graph.

## Realm-specific asset records

Each hierarchy root owns its own `Assets` provider:

```text
Server/Assets  -> assets/server
Shared/Assets  -> assets/shared
Client/Assets  -> assets/client
```

Each provider owns serializable, externally immutable `Asset` records. A record contains a realm-qualified stable asset ID, portable source path, inferred kind, SHA-256 content hash, file size, modification timestamp, importer name, imported path, and metadata.

`AssetDatabase` synchronizes one realm with its configured source directory:

```python
from somnia import Engine, Game
from somnia.assets import AssetDatabase

engine = Engine(Game())
database = AssetDatabase.from_data_model(
    engine.data_model,
    project_root=".",
    realm="shared",
)
result = database.refresh()

print(result.to_dict())
```

Use `realm="server"` for private server content and `realm="client"` for client-only content. The same relative path receives a different asset ID in each realm.

Discovery order is lexicographically deterministic. IDs remain stable when file contents change because they are derived from the realm and normalized relative path. Missing records are removed by default, and paths or symlinks that escape the configured asset root are rejected.

Project scripts and editor property edits cannot mutate imported record fields. The asset database retains an internal refresh path so source changes can update hashes and importer output while runtime instances remain separate mutable objects.

The first database slice indexes source files only. Importer execution, dependency graphs, derived artifacts, content-addressed caching, and runtime asset loading remain separate future layers.
