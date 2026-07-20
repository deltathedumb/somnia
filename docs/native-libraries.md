# Native libraries as objects

DLLs and shared objects are part of Somnia's universal object hierarchy rather than hidden build settings.

```text
DataModel
├── NativeLibraries
│   ├── Raylib
│   │   ├── InitWindow
│   │   ├── BeginDrawing
│   │   └── EndDrawing
│   └── ProjectNativeCore
└── Scripts
    └── PortaPy
```

## Object types

### `NativeLibrary`

Represents one platform-dependent library and stores:

- fallback path,
- Windows DLL path,
- Linux SO path,
- macOS dylib path,
- startup and required flags,
- whether embedded scripts may access it,
- runtime load status and diagnostics.

### `NativeFunction`

A child declaration describing:

- exported symbol,
- portable argument types,
- result type,
- calling convention,
- whether the symbol is optional.

Initial portable declarations support `int`, `float`, `bool`, `str`, `bytes`, and `none`. Structured native values will be added through an explicit ABI type registry rather than inferred from Python object layouts.

## CPython and asmpython paths

Under ordinary CPython, Somnia can use asmpython's ctypes-backed `import_binary` adapter for reference execution.

For compiled asmpython builds, `NativeLibrary.generated_binding_source()` emits static decorated declarations. This is required because the compiler needs signatures while building the executable.

Both paths originate from the same `NativeLibrary` and `NativeFunction` objects, so editor configuration and compiled bindings cannot silently drift into separate schemas.

## Security

A native library executes unrestricted machine code. Models imported from untrusted sources must not automatically load native libraries. The editor should require explicit project trust before enabling `load_on_start` or exposing a library to embedded scripts.
