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

`Engine.input_frame` retains the most recent frame. The client `InputProvider` mirrors its state and emits `input_began`, `input_changed`, `input_ended`, and `frame_updated` signals.

```python
from somnia import Engine, Game, InputProvider, RuntimeRealm
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

inputs = engine.get_provider(InputProvider)
assert inputs.is_down("KeyW")
```

`NullInputBackend` produces empty frames. `QueueInputBackend` is intended for tests, editor injection, deterministic replays, and compiler parity probes. Native window backends can implement the same `InputBackend` interface later. Rich input helpers are imported explicitly from `somnia.input` so unrelated `import somnia` builds retain the smallest compiler graph.

## Asset records

The `Assets` provider owns serializable `Asset` objects. Each record includes a stable path-derived asset ID, portable source path, inferred kind, SHA-256 content hash, file size, modification timestamp, importer name, imported path, and metadata.

`AssetDatabase` synchronizes those records with the project's configured asset directory:

```python
from somnia import Engine, Game
from somnia.assets import AssetDatabase

engine = Engine(Game())
database = AssetDatabase.from_data_model(engine.data_model, project_root=".")
result = database.refresh()

print(result.to_dict())
```

Discovery order is lexicographically deterministic. IDs remain stable when file contents change because they are derived from normalized relative paths. Missing records are removed by default, and paths that escape the configured asset root are rejected.

The first database slice indexes source files only. Importer execution, dependency graphs, derived artifacts, content-addressed caching, and runtime asset loading remain separate future layers.
