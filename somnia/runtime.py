"""Somnia engine host built around one universal DataModel."""

from __future__ import annotations

from somnia.model import (
    DataModel,
    NativeLibraryService,
    RenderService,
    ScriptService,
    World,
)
from somnia.rendering import NullRenderer


class Engine:
    """Coordinates native systems without creating a second scene structure."""

    def __init__(self, data_model=None, renderer=None):
        self.data_model = data_model or DataModel()
        self.renderer = renderer or NullRenderer()
        self.initialized = False
        self.script_hosts = []
        self.frame_number = 0
        self.install_foundation_services()

    def install_foundation_services(self):
        self.data_model.ensure_service(World)
        self.data_model.ensure_service(RenderService)
        self.data_model.ensure_service(NativeLibraryService)
        self.data_model.ensure_service(ScriptService)
        return self.data_model

    def initialize(self, native_loader=None):
        if self.initialized:
            return self
        native_libraries = self.data_model.get_service(NativeLibraryService)
        if native_libraries is not None:
            native_libraries.load_startup_libraries(loader=native_loader)
        self.renderer.initialize(self.data_model)
        self.initialized = True
        return self

    def attach_script_host(self, host):
        if host not in self.script_hosts:
            self.script_hosts.append(host)
        return host

    def start_scripts(self, context="runtime"):
        results = []
        for host in self.script_hosts:
            results.extend(host.run_auto_scripts(context=context))
        return results

    def frame(self):
        if not self.initialized:
            self.initialize()
        render_frame = self.renderer.build_frame(self.data_model)
        self.renderer.present(render_frame)
        self.frame_number += 1
        return render_frame

    def shutdown(self):
        for host in reversed(self.script_hosts):
            host.stop()
        self.script_hosts = []
        self.renderer.shutdown()
        self.initialized = False

    def clone_for_play(self):
        """Clone editor state into a separate runtime DataModel.

        Runtime objects receive new IDs and retain their source editor IDs in
        extension data. Editor-only objects are omitted by registered type name.
        """

        def clone_object(source):
            if source.type_name.startswith("somnia.editor."):
                return None
            clone = type(source)(name=source.name)
            clone.tags = list(source.tags)
            clone.extensions = dict(source.extensions)
            clone.extensions["source_object_id"] = source.object_id
            clone.apply_serialized_properties(source.serializable_properties())
            for child in source.children:
                child_clone = clone_object(child)
                if child_clone is not None:
                    clone.add_child(child_clone)
            return clone

        cloned = clone_object(self.data_model)
        if not isinstance(cloned, DataModel):
            raise RuntimeError("play clone did not produce a DataModel")
        return Engine(data_model=cloned, renderer=type(self.renderer)())
