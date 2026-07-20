# Raylib rendering

Somnia's first visual backend uses raylib through `somnia_raylib_bridge`, a
small shared library with a flat C ABI.

## Shared object structure

The renderer does not own a second scene graph. It consumes the same objects
shown by the editor and serialized by SEM/SEMJ:

```text
DataModel
├── World
│   ├── MainCamera [Camera]
│   └── Cube [MeshObject]
├── Rendering [RenderService]
└── NativeLibraries
    └── SomniaRaylibBridge [NativeLibrary]
        ├── somnia_raylib_open [NativeFunction]
        ├── somnia_raylib_begin_3d [NativeFunction]
        ├── somnia_raylib_draw_cube [NativeFunction]
        └── ...
```

`NullRenderer` and `RaylibRenderer` call the same `build_render_frame()`
function. The null backend records the frame for tests and compiler parity;
raylib translates it into native draw calls.

## First supported scene surface

- Window creation and close handling
- Target frame rate
- Perspective and orthographic cameras
- Configurable camera position, target, up vector, and field of view
- Background color
- Debug grid
- Solid and wireframe `builtin:cube` meshes
- Position and scale transforms
- Per-object RGB color and opacity

Unsupported mesh resource names are preserved in the frame and recorded by the
renderer instead of being silently discarded.

## CPython reference mode

When no bridge object is supplied, `RaylibRenderer` loads the platform library
through `CtypesRaylibBridge`:

```python
from somnia import RaylibRenderer

renderer = RaylibRenderer()
```

The bridge must exist at the platform path declared by the
`SomniaRaylibBridge` object.

## asmpython builds

The same `NativeLibrary`/`NativeFunction` hierarchy generates static
`import_binary` declarations for asmpython. This avoids maintaining a separate
handwritten ABI manifest.

The generated binding module is then wrapped as the bridge object supplied to
`RaylibRenderer`. Static adapter generation is the next integration step; the
underlying declarations and flat native ABI are already in place.

## Run the first window

Build and install the native bridge, then run:

```bash
python -m examples.raylib_cube
```

The example creates a camera and a Pixelated Purple cube using ordinary Somnia
objects and runs until the window closes.
