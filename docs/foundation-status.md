# Foundation status

## Implemented

- One registered object hierarchy for editor and runtime
- Reflected properties and object events
- Custom project/plugin object classes
- Unknown object preservation
- Editor selection and undo/redo services
- Play-mode cloning from the editor DataModel
- World, camera, mesh, light, and render service objects
- Backend-neutral rendering contract and null renderer
- NativeLibrary and NativeFunction objects
- Static asmpython binding generation from native declarations
- PortaPyRuntime and PythonScript objects
- PortaPy host boundary plus CPython reference backend
- SEMJ literal JSON models
- SEM version 1 binary envelope
- Differential CPython/asmpython runner

## Deliberately not implemented yet

- Raylib window or GPU backend
- PortaPy's concrete generated ABI adapter
- Physics simulation
- Visual editor UI
- Asset database
- RBXM/RBXMX importer
- Optimized packed SEM records
- Luau scripting

## Next vertical slice

1. Make the current CPython tests and parity snapshot green.
2. Minimize and classify any asmpython compiler failures.
3. Add a raylib native-library manifest and the smallest window/render backend.
4. Render a cube from a `MeshObject` while the null renderer remains the deterministic test oracle.
