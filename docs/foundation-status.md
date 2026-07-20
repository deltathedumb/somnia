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
- Strictly built HTML documentation
- GitHub Wiki generated from the canonical `docs/` sources

## Verification status

The current CPython reference suite passes, including:

- source compilation checks,
- unit tests,
- the foundation example,
- the deterministic scene/render snapshot.

The strict MkDocs HTML build also passes, and the same documentation source set is synchronized to the GitHub Wiki.

### Current asmpython compatibility failure

The deterministic foundation snapshot is valid under CPython, but asmpython currently rejects the program while resolving imported Somnia classes:

```text
asmpython: undefined symbol 'DataModel' has no known .so
```

Classification: **compiler rejection / whole-program import-resolution bug**.

The compiler is treating `DataModel` from `from somnia import DataModel` as an unresolved native symbol instead of merging the user package and compiling the class. This must be fixed in asmpython rather than hidden by restructuring Somnia around the limitation.

The earlier `json.dumps(..., sort_keys=True, separators=(",", ":"))` compatibility failure was fixed in asmpython's bundled JSON module; compilation now reaches the imported-class resolution stage.

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

1. Fix asmpython whole-program resolution for user packages imported from sibling project directories.
2. Re-run the unchanged CPython/asmpython deterministic snapshot.
3. Add a raylib native-library manifest and the smallest window/render backend.
4. Render a cube from a `MeshObject` while the null renderer remains the deterministic test oracle.
