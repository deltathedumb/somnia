"""Generate the static raylib bridge module used by asmpython builds."""

from __future__ import annotations

import argparse
from pathlib import Path

from somnia.rendering.raylib_codegen import generate_raylib_bridge_source


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output",
        nargs="?",
        default=".generated/raylib_native.py",
        help="generated Python module path",
    )
    parser.add_argument(
        "--platform",
        choices=("win32", "linux", "darwin"),
        default=None,
        help="target platform used to choose the DLL/SO/dylib path",
    )
    args = parser.parse_args(argv)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        generate_raylib_bridge_source(platform=args.platform),
        encoding="utf-8",
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
