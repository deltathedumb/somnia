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
import shutil
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


def show_native_backtrace(executable, *, cwd, env):
    debugger = shutil.which("gdb")
    if debugger is None:
        print("native debugger: gdb is unavailable")
        return
    traced = run(
        [
            debugger,
            "--batch",
            "-ex",
            "set pagination off",
            "-ex",
            "set disassembly-flavor intel",
            "-ex",
            "run",
            "-ex",
            "thread apply all bt full",
            "-ex",
            "info registers",
            "-ex",
            "info proc mappings",
            "-ex",
            "x/48i $pc-64",
            "-ex",
            "x/24gx $rsp",
            "--args",
            str(executable),
        ],
        cwd=cwd,
        env=env,
    )
    show_process("native gdb", traced)

    for tool, arguments in (
        ("readelf", ["-h", "-S", "-l", str(executable)]),
        ("nm", ["-n", str(executable)]),
    ):
        program = shutil.which(tool)
        if program is None:
            continue
        show_process(
            "native " + tool,
            run([program, *arguments], cwd=cwd, env=env),
        )


def make_compiler_entry(script, source_root):
    """Copy a parity script beside the src-layout package for compilation.

    asmpython currently discovers user packages relative to the entry file. A
    temporary entry directly inside ``src/`` therefore lets ``import somnia``
    resolve to ``src/somnia`` without changing the engine's public imports.
    """
    descriptor, filename = tempfile.mkstemp(
        prefix="_somnia_dualrun_",
        suffix=".py",
        dir=source_root,
    )
    os.close(descriptor)
    entry = Path(filename)
    entry.write_text(script.read_text(encoding="utf-8"), encoding="utf-8")
    return entry


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
    source_root = repo_root / "src"
    script = args.script.resolve()
    env = dict(os.environ)
    old_pythonpath = env.get("PYTHONPATH", "")
    pythonpath_parts = [str(source_root), str(repo_root)]
    if old_pythonpath:
        pythonpath_parts.append(old_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)

    reference = run([args.python, str(script)], cwd=repo_root, env=env)
    if reference.returncode != 0:
        print("ENGINE/REFERENCE FAILURE")
        show_process("CPython", reference)
        return 1

    compiler_entry = make_compiler_entry(script, source_root)
    try:
        with tempfile.TemporaryDirectory(prefix="somnia-dualrun-") as temporary:
            executable = Path(temporary) / (
                "somnia-parity.exe" if sys.platform == "win32" else "somnia-parity"
            )
            compile_command = [
                args.compiler_python,
                "-m",
                args.compiler_module,
                str(compiler_entry),
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
                show_native_backtrace(executable, cwd=repo_root, env=env)
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
    finally:
        compiler_entry.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
