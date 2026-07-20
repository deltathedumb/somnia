# Embedded Python with PortaPy

Somnia's editor and packaged runtime are intended to be compiled with asmpython. Dynamically loaded project scripts cannot be whole-program compiled ahead of time, so Somnia uses PortaPy as its embedded Python VM.

PortaPy remains a separately versioned native product. Somnia does not depend on its private VM layout or bytecode representation.

## Unified hierarchy

Embedded runtimes and scripts are normal Somnia objects:

```text
DataModel
└── Scripts
    └── PortaPy
        ├── WorldController
        └── DoorBehavior
```

- `ScriptService` owns runtime objects.
- `PortaPyRuntime` is also a `NativeLibrary`, so it uses the same DLL/SO path, trust, loading, and serialization infrastructure as other native dependencies.
- `PythonScript` stores inline source or a source path plus execution metadata.
- The Properties panel edits these objects through ordinary reflected properties.
- SEM/SEMJ serialize the same objects used by the running game.

## Runtime boundary

`ScriptHost` schedules `PythonScript` objects. It delegates evaluation to an `EmbeddedPythonBackend`.

- `PortaPyBackend` is the production backend and consumes a generated binding for PortaPy's public C ABI.
- `CPythonReferenceBackend` exists only for differential testing and development diagnostics.

The generated PortaPy ABI adapter owns exact symbol names and versioned structures. Somnia depends on semantic operations:

- create runtime,
- execute UTF-8 source,
- evaluate an expression,
- exchange checked values,
- retrieve structured errors,
- interrupt execution,
- destroy runtime.

## Host API

Embedded scripts receive a controlled Somnia host object rather than native object pointers. The host exposes safe handles into the same `DataModel` used by the editor and runtime.

PortaPy host callbacks should eventually provide:

- output and diagnostics,
- model lookup and reflected property access,
- event subscription,
- controlled asset access,
- a configurable clock,
- optional filesystem/import access.

Filesystem, network, process, and native-library access are denied by default and enabled only through explicit `PortaPyRuntime` properties and project trust.

## No Luau roadmap

Luau is not an intended Somnia scripting backend. Roblox import work, when added, will import models and metadata without promising execution of Roblox scripts.
