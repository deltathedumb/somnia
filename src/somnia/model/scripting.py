"""Embedded Python objects built on the same Somnia hierarchy as the editor."""

from __future__ import annotations

from .core import Folder, Property, Service, register_object_class
from .native import NativeLibrary


@register_object_class("somnia.PythonScript")
class PythonScript(Folder):
    """Dynamically executed project Python source hosted by PortaPy."""

    source_path = Property("", value_type=str, category="Script")
    source = Property("", value_type=str, category="Script")
    auto_run = Property(True, value_type=bool, category="Script")
    execution_context = Property("shared", value_type=str, category="Script")
    isolated_globals = Property(True, value_type=bool, category="Script")

    def __init__(self, object_id=None, name=None):
        super().__init__(object_id=object_id, name=name or "PythonScript")

    def validate_script(self):
        if self.execution_context not in (
            "server",
            "client",
            "shared",
            "editor",
            "runtime",
        ):
            raise ValueError("unsupported script execution context: " + self.execution_context)
        if not self.source and not self.source_path:
            raise ValueError("PythonScript requires source or source_path")

    def runs_in_realm(self, realm):
        if self.execution_context in ("shared", "runtime"):
            return realm in ("server", "client", "runtime")
        return self.execution_context == realm


@register_object_class("somnia.PortaPyRuntime")
class PortaPyRuntime(NativeLibrary):
    """A project-owned embedded Python VM implemented by PortaPy.

    PortaPy is loaded through the same NativeLibrary structure available to all
    projects. Runtime handles and value handles remain non-serialized host state.
    """

    requested_abi_version = Property(1, value_type=int, category="PortaPy")
    memory_limit_bytes = Property(0, value_type=int, category="PortaPy", minimum=0)
    allow_filesystem = Property(False, value_type=bool, category="PortaPy")
    allow_network = Property(False, value_type=bool, category="PortaPy")
    allow_process = Property(False, value_type=bool, category="PortaPy")
    deterministic_clock = Property(False, value_type=bool, category="PortaPy")
    runtime_created = Property(
        False,
        value_type=bool,
        serializable=False,
        category="Runtime",
        read_only=True,
    )

    def __init__(self, object_id=None, name=None):
        super().__init__(object_id=object_id, name=name or "PortaPy")
        if not self.windows_path:
            self.windows_path = "portapy.dll"
        if not self.linux_path:
            self.linux_path = "libportapy.so"
        if not self.macos_path:
            self.macos_path = "libportapy.dylib"
        self._runtime_handle = None

    def scripts(self):
        return [
            obj
            for obj in self.walk(include_self=False)
            if isinstance(obj, PythonScript)
        ]

    def sandbox_policy(self):
        return {
            "filesystem": self.allow_filesystem,
            "network": self.allow_network,
            "process": self.allow_process,
            "memory_limit_bytes": self.memory_limit_bytes,
            "deterministic_clock": self.deterministic_clock,
        }

    def mark_runtime_created(self, handle):
        self._runtime_handle = handle
        self._loading = True
        self.runtime_created = handle is not None
        self._loading = False

    def mark_runtime_destroyed(self):
        self._runtime_handle = None
        self._loading = True
        self.runtime_created = False
        self._loading = False


@register_object_class("somnia.ScriptService")
class ScriptService(Service):
    """Deprecated general script container retained for model compatibility.

    New projects place scripts under ServerScriptProvider or
    PlayerScriptProvider and may place PortaPyRuntime objects beneath either.
    """

    def __init__(self, object_id=None, name=None):
        super().__init__(object_id=object_id, name=name or "Scripts")

    def runtimes(self):
        return [
            obj
            for obj in self.walk(include_self=False)
            if isinstance(obj, PortaPyRuntime)
        ]

    def default_runtime(self):
        runtimes = self.runtimes()
        if runtimes:
            return runtimes[0]
        runtime = PortaPyRuntime()
        self.add_child(runtime)
        return runtime

    def scripts(self, context=None):
        result = []
        for runtime in self.runtimes():
            for script in runtime.scripts():
                if context is None or script.runs_in_realm(context):
                    result.append(script)
        return result
