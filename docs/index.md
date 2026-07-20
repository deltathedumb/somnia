# Somnia Engine

Somnia is a standalone, local-first game engine built around ordinary Python-shaped code compiled with [asmpython](https://github.com/deltathedumb/asmpython).

Its editor follows one foundational rule:

> The hierarchy displayed by the editor is the same registered object hierarchy used by the runtime, serializers, native integrations, and project extensions.

Somnia borrows the approachable object-tree, Properties panel, and immediate play workflow associated with Roblox Studio without becoming a hosted platform. Developers own and distribute the games they build.

## Foundation

The initial engine foundation includes:

- A universal `DataModel` shared by editor and runtime
- Reflected properties that drive inspection, serialization, and undo/redo
- Registered custom object classes
- Unknown plugin-object preservation
- `.semj` literal JSON models and `.sem` binary models
- First-class DLL, SO, and dylib objects
- PortaPy runtime and Python script objects
- A backend-neutral renderer with a deterministic null backend
- CPython/asmpython differential testing

## Start here

- [Unified object architecture](architecture.md)
- [Editor data model](editor-model.md)
- [SEM and SEMJ formats](model-formats.md)
- [Native-library objects](native-libraries.md)
- [Embedded Python with PortaPy](embedded-python.md)
- [Current foundation status](foundation-status.md)

## Build and test

```bash
python -m unittest discover -s tests -v
python -m examples.foundation
python tools/dualrun.py tests/parity/model_snapshot.py
```

## Build the HTML documentation

```bash
python -m pip install -r requirements-docs.txt
mkdocs build --strict
```

The generated website is written to `site/`.

<!-- Final temporary verification marker. -->
