"""First-class DLL/SO declarations in Somnia's universal object model."""

from __future__ import annotations

import sys

from .core import Folder, Property, Service, register_object_class


PORTABLE_ABI_TYPES = (
    "int",
    "float",
    "bool",
    "str",
    "bytes",
    "none",
)


@register_object_class("somnia.NativeFunction")
class NativeFunction(Folder):
    """A serializable function export declaration beneath a NativeLibrary."""

    symbol = Property("", value_type=str, category="Native Function")
    arguments = Property([], value_type=list, category="Native Function")
    result = Property("int", value_type=str, category="Native Function")
    calling_convention = Property("cdecl", value_type=str, category="Native Function")
    optional = Property(False, value_type=bool, category="Native Function")

    def __init__(self, object_id=None, name=None):
        super().__init__(object_id=object_id, name=name or "NativeFunction")

    def export_name(self):
        return self.symbol or self.name

    def validate_declaration(self):
        if self.calling_convention not in ("cdecl", "stdcall"):
            raise ValueError("unsupported calling convention: " + self.calling_convention)
        for value in self.arguments:
            if value not in PORTABLE_ABI_TYPES or value == "none":
                raise ValueError("unsupported native argument type: " + str(value))
        if self.result not in PORTABLE_ABI_TYPES:
            raise ValueError("unsupported native result type: " + str(self.result))
        if not self.export_name():
            raise ValueError("native function requires a symbol or object name")

    def generated_stub(self, library_variable="library"):
        """Return static Python source suitable for asmpython compilation."""
        self.validate_declaration()
        argument_parts = []
        for index, type_name in enumerate(self.arguments):
            argument_parts.append("arg" + str(index) + ": " + type_name)
        return_type = "None" if self.result == "none" else self.result
        lines = [
            "@" + library_variable + ".imported",
            "def " + self.export_name() + "(" + ", ".join(argument_parts) + ") -> " + return_type + ":",
            "    pass",
        ]
        return "\n".join(lines)


@register_object_class("somnia.NativeLibrary")
class NativeLibrary(Folder):
    """A project-owned DLL/SO and its child NativeFunction declarations."""

    path = Property("", value_type=str, category="Native Library")
    windows_path = Property("", value_type=str, category="Native Library")
    linux_path = Property("", value_type=str, category="Native Library")
    macos_path = Property("", value_type=str, category="Native Library")
    load_on_start = Property(True, value_type=bool, category="Native Library")
    required = Property(True, value_type=bool, category="Native Library")
    expose_to_scripts = Property(False, value_type=bool, category="Native Library")
    loaded = Property(
        False,
        value_type=bool,
        serializable=False,
        category="Runtime",
        read_only=True,
    )
    last_error = Property(
        "",
        value_type=str,
        serializable=False,
        category="Runtime",
        read_only=True,
    )

    def __init__(self, object_id=None, name=None):
        super().__init__(object_id=object_id, name=name or "NativeLibrary")
        self._native_handle = None

    def selected_path(self, platform=None):
        current = platform or sys.platform
        if current == "win32" and self.windows_path:
            return self.windows_path
        if current.startswith("linux") and self.linux_path:
            return self.linux_path
        if current == "darwin" and self.macos_path:
            return self.macos_path
        return self.path

    def functions(self):
        return [child for child in self.children if isinstance(child, NativeFunction)]

    def validate_declaration(self, platform=None):
        if not self.selected_path(platform=platform):
            raise ValueError("native library has no path for the selected platform")
        for function in self.functions():
            function.validate_declaration()

    def generated_binding_source(self, variable_name="library", platform=None):
        """Generate a static binding module consumed by asmpython builds."""
        self.validate_declaration(platform=platform)
        selected = self.selected_path(platform=platform)
        lines = [
            "from asmpython import import_binary",
            "",
            variable_name + " = import_binary(" + repr(selected) + ")",
            "",
        ]
        for function in self.functions():
            lines.append(function.generated_stub(variable_name))
            lines.append("")
        return "\n".join(lines)

    def load_reference(self, loader=None):
        """Load through CPython's asmpython import_binary adapter.

        The production asmpython path uses generated static bindings because the
        compiler must know function signatures at build time.
        """
        if loader is None:
            from asmpython import import_binary

            loader = import_binary
        try:
            self._native_handle = loader(self.selected_path())
            self._loading = True
            self.loaded = True
            self.last_error = ""
            self._loading = False
            return self._native_handle
        except Exception as error:
            self._loading = True
            self.loaded = False
            self.last_error = str(error)
            self._loading = False
            if self.required:
                raise
            return None

    def unload_reference(self):
        self._native_handle = None
        self._loading = True
        self.loaded = False
        self._loading = False


@register_object_class("somnia.NativeLibraryService")
class NativeLibraryService(Service):
    """Owns project native libraries in both editor and runtime DataModels."""

    def __init__(self, object_id=None, name=None):
        super().__init__(object_id=object_id, name=name or "NativeLibraries")

    def libraries(self):
        return [child for child in self.children if isinstance(child, NativeLibrary)]

    def load_startup_libraries(self, loader=None):
        loaded = []
        for library in self.libraries():
            if library.enabled and library.load_on_start:
                handle = library.load_reference(loader=loader)
                if handle is not None:
                    loaded.append(library)
        return loaded

    def generate_project_bindings(self, platform=None):
        modules = {}
        for library in self.libraries():
            safe_name = "".join(
                character if character.isalnum() else "_"
                for character in library.name.lower()
            ).strip("_")
            if not safe_name:
                safe_name = "native_library"
            modules[safe_name + "_native.py"] = library.generated_binding_source(
                platform=platform
            )
        return modules
