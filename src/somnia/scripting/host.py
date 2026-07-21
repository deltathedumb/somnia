"""Embedded Python host boundary for Somnia.

Somnia's production embedded runtime is PortaPy. CPython remains available as a
reference backend for tests and editor diagnostics, not as a packaged runtime
requirement.
"""

from __future__ import annotations


class ScriptExecutionError(RuntimeError):
    def __init__(self, message, script_name="", traceback_text=""):
        super().__init__(message)
        self.script_name = script_name
        self.traceback_text = traceback_text


class EmbeddedPythonBackend:
    backend_name = "base"

    def start(self, runtime_object, host_api):
        raise NotImplementedError

    def execute(self, runtime_handle, source, filename, globals_dict=None):
        raise NotImplementedError

    def evaluate(self, runtime_handle, expression, filename, globals_dict=None):
        raise NotImplementedError

    def stop(self, runtime_handle):
        raise NotImplementedError


class CPythonReferenceBackend(EmbeddedPythonBackend):
    """Behavioral-reference backend used by tests and development tools."""

    backend_name = "cpython-reference"

    def start(self, runtime_object, host_api):
        return {
            "globals": {
                "__builtins__": __builtins__,
                "somnia": host_api,
            }
        }

    def execute(self, runtime_handle, source, filename, globals_dict=None):
        namespace = runtime_handle["globals"]
        if globals_dict:
            namespace.update(globals_dict)
        code = compile(source, filename, "exec")
        exec(code, namespace, namespace)
        return None

    def evaluate(self, runtime_handle, expression, filename, globals_dict=None):
        namespace = runtime_handle["globals"]
        if globals_dict:
            namespace.update(globals_dict)
        code = compile(expression, filename, "eval")
        return eval(code, namespace, namespace)

    def stop(self, runtime_handle):
        runtime_handle.clear()


class PortaPyBackend(EmbeddedPythonBackend):
    """Adapter around a generated binding for PortaPy's public C ABI.

    The adapter object is deliberately injected because PortaPy's ABI remains a
    separately versioned product boundary. Somnia depends only on these semantic
    operations, while generated bindings own exact symbol names and structures.
    """

    backend_name = "portapy"

    def __init__(self, abi_adapter):
        self.abi = abi_adapter

    def start(self, runtime_object, host_api):
        runtime_object.load_reference(loader=getattr(self.abi, "library_loader", None))
        handle = self.abi.create_runtime(
            requested_abi_version=runtime_object.requested_abi_version,
            policy=runtime_object.sandbox_policy(),
            host_api=host_api,
        )
        if handle is None:
            raise ScriptExecutionError("PortaPy failed to create a runtime")
        return handle

    def execute(self, runtime_handle, source, filename, globals_dict=None):
        return self.abi.execute_source(
            runtime_handle,
            source=source,
            filename=filename,
            globals_dict=globals_dict or {},
        )

    def evaluate(self, runtime_handle, expression, filename, globals_dict=None):
        return self.abi.evaluate_expression(
            runtime_handle,
            expression=expression,
            filename=filename,
            globals_dict=globals_dict or {},
        )

    def stop(self, runtime_handle):
        self.abi.destroy_runtime(runtime_handle)


class ScriptHost:
    """Runs PythonScript objects through one PortaPyRuntime object."""

    def __init__(self, runtime_object, backend, host_api, game=None):
        self.runtime_object = runtime_object
        self.backend = backend
        self.host_api = host_api
        self.game = game
        self.runtime_handle = None

    @property
    def started(self):
        return self.runtime_handle is not None

    def bind_game(self, game):
        self.game = game
        return self

    def resolve_game(self):
        if self.game is not None:
            return self.game
        node = self.runtime_object
        while node is not None:
            if getattr(node, "type_name", "") == "somnia.Game":
                self.game = node
                return node
            node = node.parent
        return None

    def start(self):
        if self.started:
            return self.runtime_handle
        self.runtime_handle = self.backend.start(self.runtime_object, self.host_api)
        self.runtime_object.mark_runtime_created(self.runtime_handle)
        return self.runtime_handle

    def execute_script(self, script, extra_globals=None):
        script.validate_script()
        if not self.started:
            self.start()
        source = script.source
        filename = script.source_path or ("<" + script.name + ">")
        if not source and script.source_path:
            if not self.runtime_object.allow_filesystem:
                raise ScriptExecutionError(
                    "script source_path requires filesystem permission",
                    script_name=script.name,
                )
            with open(script.source_path, "r", encoding="utf-8") as source_file:
                source = source_file.read()
        script_globals = dict(extra_globals or {})
        game = self.resolve_game()
        if game is not None:
            script_globals["game"] = game
        try:
            return self.backend.execute(
                self.runtime_handle,
                source,
                filename,
                globals_dict=script_globals,
            )
        except ScriptExecutionError:
            raise
        except Exception as error:
            raise ScriptExecutionError(str(error), script_name=script.name) from error

    def run_auto_scripts(self, context="runtime"):
        results = []
        for script in self.runtime_object.scripts():
            if not script.enabled or not script.auto_run:
                continue
            if script.execution_context not in (context, "shared"):
                continue
            results.append((script, self.execute_script(script)))
        return results

    def stop(self):
        if self.runtime_handle is None:
            return
        self.backend.stop(self.runtime_handle)
        self.runtime_handle = None
        self.runtime_object.mark_runtime_destroyed()
