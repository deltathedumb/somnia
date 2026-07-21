# Somnia Engine

Somnia is a local-first game engine built around Python-shaped code compiled with [asmpython](https://github.com/deltathedumb/asmpython).

The project borrows the approachable object hierarchy, Properties editing, and immediate play workflow of Roblox Studio without becoming a hosted platform. Games made with Somnia are ordinary projects that developers own and distribute themselves.

## Foundation goals

- Python is the primary engine and gameplay language.
- CPython is the behavioral reference implementation.
- asmpython is the production compiler.
- Valid Python that fails only under asmpython is fixed in asmpython rather than hidden through awkward Somnia source.
- The editor and runtime use the same registered object hierarchy.
- Providers are root-level singleton game systems, equivalent to Roblox services.
- Objects such as parts should behave sensibly by default; replaceable backends remain implementation details.
- Rendering is accessed through a replaceable backend boundary; raylib is the first native backend.
- Physics exposes a small, approachable public interface while permitting custom or replacement backends.
- Somnia models use `.semj` for literal JSON source models and `.sem` for compact binary models.
- Luau is not an intended scripting backend.

## Canonical game hierarchy

```text
Game
├── Scene
├── Environment
├── ServerScriptProvider
├── ServerStorage
├── SharedStorage
├── ClientStorage
├── PlayerProvider
├── PlayerScriptProvider
├── PlayerUIProvider
├── Assets
├── PhysicsProvider       [hidden]
├── NetworkProvider       [hidden]
├── HttpProvider          [hidden]
├── AnimationProvider     [hidden]
├── AudioProvider         [hidden]
├── InputProvider         [hidden]
├── TimeProvider          [hidden]
├── NavigationProvider    [hidden]
└── LocalizationProvider  [hidden]
```

Hidden providers are still ordinary accessible objects; they are only omitted from the default Explorer view.

## Export types

- **Client** — client runtime plus a separate invisible integrated server runtime. This is the ordinary standalone/single-player export.
- **DedicatedServer** — authoritative headless server only.
- **DedicatedClient** — client only, with no bundled server code; intended for games using proprietary or separately hosted servers.

Exporting clones the authored `Game` into physically separate server and client DataModels. A `DedicatedClient` does not contain `ServerStorage`, `ServerScriptProvider`, or their descendants.

## Current status

The repository currently contains:

- One registered object model for editor, runtime, providers, serialization, and custom classes
- The complete canonical provider set and hidden-provider Explorer filtering
- Client/server realm metadata and export partitioning
- Independent integrated-server and client play DataModels
- Custom object classes with reflected Properties support
- First-class DLL/SO declarations and PortaPy runtime objects
- `.semj` JSON and `.sem` binary serialization
- A raylib rendering boundary plus deterministic null renderer
- CPython/asmpython differential execution tooling
- Strict HTML documentation and synchronized GitHub Wiki documentation

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
    model/         Universal objects and providers
    formats/       SEM and SEMJ codecs
    rendering/     Renderer contracts and backends
    build.py       Client/server export partitioning
examples/          Small runnable engine slices
tests/             CPython unit and cross-runtime parity tests
tools/             Developer and compiler-differential tools
docs/              HTML/Wiki source documentation
```

## License

Somnia Engine is licensed under the [Mozilla Public License 2.0](LICENSE).

The MPL applies at the source-file level. Games, scripts, plugins, models, assets, and other separate project files do not become MPL-licensed merely because they use Somnia. When distributing modified Somnia-covered files, those files and their source must remain available under MPL-2.0. Third-party dependencies remain governed by their own licenses.

Somnia Engine is developed by Pixelated Dream.
