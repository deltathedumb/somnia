"""Run one Somnia behavior under CPython and compiled asmpython.

Exit codes:
  0 parity pass
  1 CPython/reference failure
  2 asmpython compile failure
  3 compiled executable failure
  4 observable output mismatch
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run(command, *, cwd, env):
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def show_process(label, result):
    print(label + ": return code " + str(result.returncode))
    if result.stdout:
        print(label + " stdout:")
        print(result.stdout.rstrip())
    if result.stderr:
        print(label + " stderr:")
        print(result.stderr.rstrip())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", type=Path)
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="reference CPython executable",
    )
    parser.add_argument(
        "--compiler-python",
        default=sys.executable,
        help="Python executable used to invoke the asmpython compiler",
    )
    parser.add_argument(
        "--compiler-module",
        default="asmpython",
        help="module used as `python -m MODULE`",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    script = args.script.resolve()
    env = dict(os.environ)
    old_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(repo_root) + (os.pathsep + old_pythonpath if old_pythonpath else "")

    reference = run([args.python, str(script)], cwd=repo_root, env=env)
    if reference.returncode != 0:
        print("ENGINE/REFERENCE FAILURE")
        show_process("CPython", reference)
        return 1

    with tempfile.TemporaryDirectory(prefix="somnia-dualrun-") as temporary:
        executable = Path(temporary) / (
            "somnia-parity.exe" if sys.platform == "win32" else "somnia-parity"
        )
        compile_command = [
            args.compiler_python,
            "-m",
            args.compiler_module,
            str(script),
            "-o",
            str(executable),
        ]
        compiled = run(compile_command, cwd=repo_root, env=env)
        if compiled.returncode != 0 or not executable.exists():
            print("ASMPYTHON COMPILER REJECTION")
            print("Source works under CPython but did not produce a native executable.")
            show_process("CPython", reference)
            show_process("asmpython compile", compiled)
            return 2

        native = run([str(executable)], cwd=repo_root, env=env)
        if native.returncode != 0:
            print("ASMPYTHON COMPILED-RUNTIME FAILURE")
            print("Compilation succeeded, but the native executable failed.")
            show_process("CPython", reference)
            show_process("native", native)
            return 3

        if reference.stdout != native.stdout:
            print("ASMPYTHON OBSERVABLE MISCOMPILE")
            print("Both executions completed but produced different stdout.")
            show_process("CPython", reference)
            show_process("native", native)
            return 4

        print("PARITY PASS")
        print(reference.stdout.rstrip())
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
