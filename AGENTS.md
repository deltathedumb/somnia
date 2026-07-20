# Somnia Agent Guide

## Product definition

Somnia is a standalone, local-first game engine. It is not a Roblox-like hosting platform, social platform, marketplace, or mandatory cloud service.

The editor may borrow productive ideas from Roblox Studio—scene hierarchy, property inspection, live play, and approachable object scripting—without inheriting platform lock-in.

## Language and compiler policy

1. Write engine source as clear, ordinary Python.
2. CPython is the behavioral reference.
3. asmpython is the production compiler.
4. Run meaningful behavior through both runtimes whenever possible.
5. When CPython succeeds and asmpython fails, classify the result explicitly as one of:
   - compiler rejection,
   - miscompile,
   - runtime gap,
   - FFI gap,
   - intentional language difference.
6. Do not deform clean engine architecture merely to conceal an asmpython limitation. Add a focused reproducer and either fix asmpython or use a clearly documented temporary workaround.

## Object model

- Every serializable object has a stable ID and registered type name.
- Projects and plugins may register custom object classes.
- Serializers preserve unknown object types and properties rather than silently deleting them.
- Runtime-only state must not leak into `.semj` or `.sem` unless explicitly declared serializable.
- Parent/child relations are stored through stable IDs, not Python object addresses.

## Model formats

- `.semj` is literal UTF-8 JSON.
- `.sem` is the binary representation of the same logical schema.
- Conversion between `.semj` and `.sem` must be lossless for supported values.
- Format versions are explicit and validated.
- Unknown extension data should be preserved when practical.

## Scripting scope

Python/asmpython is the intended scripting system. Luau support is not on the roadmap unless the product direction is explicitly changed later.

## Near-term architecture

- `somnia.math`: value math
- `somnia.model`: object registry and hierarchy
- `somnia.formats`: SEM/SEMJ codecs
- `somnia.rendering`: backend-neutral render contract
- `tools/dualrun.py`: CPython/asmpython comparison

Keep the public API independent from raylib so the renderer can be replaced later.
