# Somnia architecture

## One object model everywhere

Somnia follows one defining rule:

> The editor, runtime, imported models, project configuration, services, and custom extensions all operate on the same registered object structure.

This is similar to Roblox Studio's data-model workflow: the hierarchy shown by the editor is the real hierarchy used by the running game. The editor does not maintain a second private representation and translate it into runtime objects later.

## Universal objects

Every object derives from `SomniaObject` and provides:

- a stable object ID,
- a registered serialization type,
- a human-readable name,
- a parent and ordered children,
- reflected properties,
- optional tags,
- lifecycle hooks,
- extension data for unknown or future fields.

Objects can represent visible scene entities, logical managers, resources, editor-owned state, or project services.

```text
DataModel
├── World
│   ├── Camera
│   ├── Model
│   │   ├── MeshObject
│   │   └── CustomProjectObject
│   └── Environment
├── Assets
├── Input
├── Physics
└── Editor (editor process only)
    ├── Selection
    ├── History
    └── Viewports
```

The `Editor` branch is omitted from packaged games, but it uses the same object registry, property metadata, hierarchy operations, and event model.

## Reflection

Object classes declare serializable/editor-visible properties with `Property` descriptors. The same metadata drives:

- the Properties panel,
- SEM/SEMJ serialization,
- cloning,
- undo/redo commands,
- change notifications,
- validation,
- future networking/replication metadata.

This avoids maintaining separate editor schemas and runtime schemas.

## Custom object classes

Projects and plugins register subclasses with a stable type name:

```python
@register_object_class("my_game.Door")
class Door(ModelNode):
    open_speed = Property(2.0, value_type=float, minimum=0.0)
    locked = Property(False, value_type=bool)
```

The type name—not the Python module object's memory identity—is stored in `.semj` and `.sem`.

If the class is unavailable while loading, Somnia creates an `UnknownModelNode` that preserves:

- original type name,
- all serialized properties,
- child hierarchy,
- extension data.

Installing the missing plugin later can rehydrate the preserved node.

## Editor behavior

The Scene Tree is a view of the real object hierarchy. The Properties panel reads the selected object's property metadata. Creating, renaming, parenting, or editing an object executes commands against the same live model used by play mode.

Play-in-editor can clone the editable `DataModel` into a runtime `DataModel`, preserving stable source IDs for debugging while assigning separate runtime identities where needed.

## Native systems

Rendering, audio, and high-performance physics may keep native backing storage, but the public object remains a registered Somnia object containing safe native handles. Native systems never become a competing user-visible hierarchy.

## Scripting

Python/asmpython is the intended scripting system. Custom behavior classes participate in the same registry and reflection system. Luau is not an intended feature.
