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
- Raylib renderer backed by a flat Somnia-owned C bridge ABI
- Window, camera, grid, solid-cube, and wireframe-cube rendering
- NativeLibrary and NativeFunction objects
- Static asmpython binding generation from native declarations
- Generated typed raylib bridge adapter for asmpython
- PortaPyRuntime and PythonScript objects
- PortaPy host boundary plus CPython reference backend
- SEMJ literal JSON models
- SEM version 1 binary envelope
- Differential CPython/asmpython runner
- Standard `src/somnia` package layout
- Strictly built HTML documentation
- GitHub Wiki generated from the canonical `docs/` sources

## Verification status

The current CPython reference suite passes, including:

- editable installation from the `src/` layout,
- source compilation checks,
- unit tests,
- the foundation example,
- the deterministic scene/render snapshot,
- generated raylib adapter tests.

The deterministic foundation snapshot also compiles and produces matching output under asmpython. The receiver-rule audit and whole-program import-graph audit pass in CI.

The strict MkDocs HTML build also passes, and the same documentation source set is synchronized to the GitHub Wiki.

### asmpython package-root workaround

asmpython currently discovers user packages relative to the compiled entry file. Somnia therefore keeps its public package at `src/somnia` and places a temporary compiler entry directly inside `src/` during differential runs. This makes `import somnia` resolve as ordinary project source without changing Somnia's public API.

This removes the former rejection:

```text
asmpython: undefined symbol 'DataModel' has no known .so
```

The workaround is isolated to `tools/dualrun.py` and CI diagnostics. CPython runs the original source file unchanged. The broader compiler limitation for entry files outside their source root remains an asmpython issue, but it no longer blocks Somnia development.

## Deliberately not implemented yet

- PortaPy's concrete generated ABI adapter
- Physics simulation
- Visual editor UI
- Asset database
- RBXM/RBXMX importer
- Optimized packed SEM records
- Luau scripting

## Next vertical slice

1. Build the native raylib bridge automatically in CI.
2. Compile the generated raylib adapter with asmpython as a focused compatibility target.
3. Add a deterministic input/event frame contract beside the render-frame contract.
4. Begin the asset database required by meshes, textures, scripts, and editor browsing.
