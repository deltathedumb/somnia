# Foundation status

## Implemented

- One registered object hierarchy for editor and runtime
- Reflected properties and object events
- Custom project/plugin object classes
- Unknown object preservation
- Editor selection and undo/redo services
- Play-mode cloning from the editor DataModel
- Fixed `Server`, `Shared`, and `Client` realm roots as the only top-level `Game` objects
- Canonical providers grouped beneath their packaging realm
- Hierarchical scripting access such as `game.server.PhysicsProvider`
- Automatic migration of legacy flat top-level providers into canonical roots
- Exact export root contracts: Client=`Shared + Client`, DedicatedClient=`Client`, DedicatedServer=`Server + Shared`
- Runtime preservation of explicitly packaged root sets
- World, camera, mesh, light, and render service objects
- Backend-neutral rendering contract and null renderer
- Raylib renderer backed by a flat Somnia-owned C bridge ABI
- Window, camera, grid, solid-cube, and wireframe-cube rendering
- Deterministic backend-neutral input frames
- Null and queued input backends for headless runs, tests, editor injection, and replays
- InputProvider state snapshots and transition signals
- Separate Server, Shared, and Client Assets providers
- Externally immutable serialized Asset records
- Deterministic realm-qualified asset IDs, discovery, hashing, kind inference, stale-record removal, and symlink-aware root containment
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
- Pull-request workflow concurrency that cancels superseded CI and documentation runs

## Verification status

The CPython reference suite covers:

- editable installation from the `src/` layout,
- source compilation checks,
- unit tests,
- the foundation example,
- the deterministic scene/render snapshot,
- generated raylib adapter tests,
- fixed realm-root hierarchy and script access,
- exact export root combinations,
- preservation of a DedicatedClient's Client-only root set,
- legacy flat-provider migration,
- deterministic input state and signals,
- realm-specific immutable asset add/update/remove behavior and path containment.

The strict MkDocs HTML build and Wiki synchronization use the same canonical documentation source set.

### Current asmpython compatibility work

Somnia keeps its public package at `src/somnia` and places temporary compiler entries directly inside `src/` during differential runs. This works around asmpython's current package-root discovery limitation without changing Somnia's public API.

The expanded provider/export snapshot remains a native diagnostic target. The latest verified input-independent baseline passes whole-program import analysis and compiles successfully, but the generated executable segfaults inside asmpython's generated dictionary runtime before producing the reference snapshot. Somnia CI preserves the unchanged CPython output and uploads compiler audits, native diagnostics, and the failing executable trace. Optional input replay/serialization and filesystem asset tooling are kept outside the core import graph so they do not widen this known compiler-runtime gap.

## Deliberately not implemented yet

- PortaPy's concrete generated ABI adapter
- Physics simulation
- Visual editor UI
- Native raylib input adapter
- Asset importer execution and dependency graphs
- Derived-asset cache and runtime asset loading
- RBXM/RBXMX importer
- Optimized packed SEM records
- Luau scripting

## Next vertical slice

1. Build the native raylib bridge automatically in CI.
2. Compile the generated raylib adapter with asmpython as a focused compatibility target.
3. Connect raylib keyboard, mouse, and gamepad collection to the new InputBackend contract.
4. Add importer registration, dependency tracking, and content-addressed derived artifacts to the asset database.
