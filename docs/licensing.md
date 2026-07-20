# Licensing

Somnia Engine is licensed under the **Mozilla Public License 2.0** (`MPL-2.0`). The complete license text is stored in the repository root as `LICENSE`.

## What the MPL covers

The MPL applies at the source-file level. Somnia source files and distributed modifications to those covered files remain under MPL-2.0.

When distributing a modified Somnia executable or editor build, the corresponding source for the MPL-covered Somnia files must be made available under MPL-2.0. The distribution must also preserve the applicable license notices.

## Games and project content

Using Somnia does not automatically place an entire game under MPL-2.0. Separate project files may use terms chosen by their authors, including proprietary terms.

This includes separate:

- gameplay scripts,
- custom object classes,
- plugins and native libraries,
- `.sem` and `.semj` models,
- textures, audio, meshes, and other assets,
- project documentation,
- generated game-specific code.

A file that copies or modifies MPL-covered Somnia source may itself be a modification under the license. Merely importing, calling, extending, or communicating with Somnia through its public interfaces does not by itself make an otherwise separate file part of Somnia's covered source.

## Engine forks and modifications

A distributor may combine Somnia with a larger proprietary work. The larger work can use different terms, but the MPL-covered Somnia files and distributed modifications to them must remain available under MPL-2.0.

Private modifications that are not distributed do not trigger the MPL's source-distribution requirements.

## Plugins and DLL/SO integrations

Somnia's support for custom object classes, plugins, DLLs, SOs, and dylibs does not impose MPL-2.0 on independent plugin or library files merely because they use Somnia's API. Each plugin or native library may declare its own license.

Modifications copied directly into existing Somnia-covered files remain governed by MPL-2.0 when distributed.

## Third-party software

Dependencies such as asmpython, PortaPy, raylib, and future native libraries retain their own licenses. Somnia distributions must preserve any notices required by those dependencies.

## Trademark

MPL-2.0 does not grant rights to Pixelated Dream's names, logos, service marks, or other branding beyond what is necessary to comply with license notices. A separate trademark policy may be added as Somnia's public identity develops.

## Source notice

Somnia uses the standard MPL Exhibit A notice:

> This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

The root `LICENSE` and `NOTICE` files provide the repository-wide license notice. Individual source files may also include the Exhibit A notice.

This page is a practical project summary. The full `LICENSE` text controls if this summary and the license differ.
