# Somnia Engine

Somnia is a local-first, standalone game engine built around Python-shaped code compiled with [asmpython](https://github.com/deltathedumb/asmpython).

The project borrows the approachable scene hierarchy, property editing, and immediate play workflow of Roblox Studio without becoming a hosted platform. Games made with Somnia are ordinary standalone projects that developers own and distribute themselves.

## Foundation goals

- Python is the primary engine and gameplay language.
- CPython is the behavioral reference implementation.
- asmpython is the production compiler.
- Any source that works in CPython but fails or behaves differently under asmpython is reported as an asmpython compatibility failure, not hidden as an engine bug.
- Rendering is accessed through a replaceable backend boundary; raylib is the intended first native backend.
- Physics will be developed as a Somnia-owned subsystem rather than delegated permanently to a third-party engine.
- Somnia models use `.semj` for literal JSON source models and `.sem` for compact binary models.
- Luau is not an intended scripting backend.

## Current status

This repository contains the first engine foundation:

- Core math values (`Vec3`, `Quaternion`, and `Transform`)
- Stable-ID model nodes and hierarchy validation
- `.semj` JSON serialization
- `.sem` binary serialization
- A renderer interface and deterministic null renderer
- CPython/asmpython differential execution tooling
- Initial model-format and architecture documentation

## Quick start

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m examples.foundation
```

To compare CPython behavior with an asmpython-compiled executable:

```bash
python tools/dualrun.py tests/parity/model_snapshot.py
```

The dual runner requires an accessible asmpython checkout or installation.

## Repository layout

```text
src/
  somnia/
    math/          Engine math values
    model/         Serializable model graph
    formats/       SEM and SEMJ codecs
    rendering/     Renderer contracts and test backend
examples/          Small runnable engine slices
tests/             CPython unit and cross-runtime parity tests
tools/             Developer and compiler-differential tools
docs/              Architecture and format specifications
```

## License

Somnia Engine is licensed under the [Mozilla Public License 2.0](LICENSE).

The MPL applies at the source-file level. Games, scripts, plugins, models, assets, and other separate project files do not become MPL-licensed merely because they use Somnia. When distributing modified Somnia-covered files, those files and their source must remain available under MPL-2.0. Third-party dependencies remain governed by their own licenses.

Somnia Engine is developed by Pixelated Dream.
