# Somnia Agent Guide

## Product definition

Somnia is a standalone, local-first game engine. It is not a Roblox-like hosting platform, social platform, marketplace, or mandatory cloud service.

The editor may borrow productive ideas from Roblox Studio—scene hierarchy, property inspection, live play, and approachable object scripting—without inheriting platform lock-in.

## License policy

- Somnia Engine is licensed under the Mozilla Public License 2.0 (`MPL-2.0`).
- Preserve the root `LICENSE` and `NOTICE` files and all applicable third-party notices.
- Distributed modifications to MPL-covered Somnia files must remain available under MPL-2.0.
- Separate games, scripts, plugins, native libraries, models, and assets are not automatically MPL-covered merely because they use Somnia.
- Do not copy third-party code into Somnia unless its license is compatible with MPL-2.0 and all required attribution is recorded.
- New documentation about licensing must remain consistent with `LICENSE`; the license text controls if a summary differs.

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
6. Do not deform clean engine architecture merely to conceal an asmpython limitation.
7. When valid Somnia Python is blocked by missing compiler, runtime, stdlib, linker, or FFI behavior, implement the missing capability in `deltathedumb/asmpython` first and add a focused asmpython regression case.
8. Temporary Somnia workarounds are allowed only when the behavior is intentionally outside Python/asmpython scope or an external dependency makes the direct implementation impossible. Document every workaround and remove it after the upstream capability exists.
9. Re-run the unchanged Somnia differential case after each asmpython fix. The clean Somnia source is the acceptance test.

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

- `somnia.math`: shared engine value math
- `somnia.model`: object registry and hierarchy
- `somnia.formats`: SEM/SEMJ codecs
- `somnia.rendering`: backend-neutral render contract
- `tools/dualrun.py`: CPython/asmpython comparison

Keep the public API independent from raylib so the renderer can be replaced later.
