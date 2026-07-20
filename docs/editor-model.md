# Editor data model

Somnia's editor is a collection of views and commands over the same `DataModel` used by the running game.

- Scene Tree: traverses `DataModel.children`.
- Properties: reads `Property` metadata from selected objects.
- Undo/redo: executes commands against live objects.
- Custom object palette: reads `ObjectRegistry`.
- Save: serializes the live hierarchy to SEMJ or SEM.
- Play: clones the hierarchy into an isolated runtime DataModel.
- Native libraries and PortaPy runtimes: appear as normal objects in the same tree.

A panel must not create its own authoritative object schema. Cached UI state is permitted, but the registered Somnia object remains the source of truth.
