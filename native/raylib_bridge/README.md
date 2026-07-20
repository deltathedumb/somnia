# Somnia raylib bridge

This shared library gives Somnia a stable, flat C ABI over raylib. No raylib
`Vector3`, `Color`, or `Camera3D` structure crosses the Python/asmpython FFI
boundary; every exported function uses only integers, floats, UTF-8 strings,
and `void` results.

## Requirements

- CMake 3.20 or newer
- A C99 compiler
- raylib with a CMake package configuration

## Build

```bash
cmake -S native/raylib_bridge -B build/raylib-bridge \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_PREFIX_PATH=/path/to/raylib
cmake --build build/raylib-bridge --config Release
cmake --install build/raylib-bridge --prefix .
```

The install step writes the platform library beneath `native/`:

```text
native/somnia_raylib_bridge.dll
native/libsomnia_raylib_bridge.so
native/libsomnia_raylib_bridge.dylib
```

The raylib runtime DLL/SO and any of its dependencies must also be discoverable
by the operating system's dynamic loader.

## Why a bridge?

Calling raw raylib functions would require matching C structure return and
argument layouts in every supported runtime and ABI. The bridge keeps Somnia's
canonical native declaration portable across:

- CPython `ctypes` reference execution
- asmpython `import_binary` native builds
- editor and game runtime processes
- Windows, Linux, and macOS
