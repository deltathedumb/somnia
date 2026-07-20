"""Somnia engine host built around provider-based client/server DataModels."""

from __future__ import annotations

from somnia.build import ExportType, create_export_plan
from somnia.model import (
    DataModel,
    Game,
    NativeLibrary,
    RuntimeRealm,
    get_provider,
    install_canonical_providers,
)
from somnia.rendering import NullRenderer


class Engine:
    """Coordinate one logical Somnia runtime realm.

    A normal Client play/export creates a client Engine plus an invisible
    integrated server Engine. Both runtimes retain separate DataModels and are
    intended to communicate through NetworkProvider rather than shared objects.
    """

    def __init__(self, data_model=None, renderer=None, realm=RuntimeRealm.PROJECT):
        normalized_realm = RuntimeRealm.normalize(realm)
        if data_model is None:
            data_model = Game(realm=normalized_realm)
        self.data_model = data_model
        self.realm = normalized_realm
        if isinstance(self.data_model, Game):
            self.data_model.realm = normalized_realm
        self.renderer = renderer or NullRenderer()
        self.initialized = False
        self.script_hosts = []
        self.frame_number = 0
        self.delta_time = 0.0
        self.integrated_server = None
        self.install_foundation_services()

    def install_foundation_services(self):
        install_canonical_providers(self.data_model, realm=self.realm)
        return self.data_model

    def get_provider(self, provider_type_or_name, create=True):
        return get_provider(
            self.data_model,
            provider_type_or_name,
            create=create,
        )

    def initialize(self, native_loader=None):
        if self.initialized:
            return self
        for obj in self.data_model.walk(include_self=True):
            if isinstance(obj, NativeLibrary) and obj.enabled and obj.load_on_start:
                obj.load_reference(loader=native_loader)
        self.renderer.initialize(self.data_model)
        self.initialized = True
        return self

    def attach_script_host(self, host):
        if host not in self.script_hosts:
            self.script_hosts.append(host)
        return host

    def start_scripts(self, context=None):
        active_context = context or self.realm
        results = []
        for host in self.script_hosts:
            results.extend(host.run_auto_scripts(context=active_context))
        return results

    def frame(self):
        if not self.initialized:
            self.initialize()
        render_frame = self.renderer.build_frame(self.data_model)
        self.renderer.present(render_frame)
        self.delta_time = self.renderer.frame_time()
        self.frame_number += 1
        return render_frame

    def run(self, max_frames=None):
        """Run frames until the renderer closes or an optional limit is reached."""
        if not self.initialized:
            self.initialize()
        if max_frames is None and self.renderer.backend_name == "null":
            max_frames = 1
        frames = []
        while not self.renderer.should_close():
            frames.append(self.frame())
            if max_frames is not None and len(frames) >= max_frames:
                break
        return frames

    def shutdown(self):
        for host in reversed(self.script_hosts):
            host.stop()
        self.script_hosts = []
        self.renderer.shutdown()
        self.initialized = False
        if self.integrated_server is not None:
            server = self.integrated_server
            self.integrated_server = None
            server.shutdown()

    def create_export_plan(self, export_type):
        if not isinstance(self.data_model, Game):
            raise TypeError("exports require a canonical somnia.Game root")
        return create_export_plan(self.data_model, export_type)

    def clone_for_play(self):
        """Create a Client play session with a separate invisible local server.

        The returned value is the client Engine for backward compatibility. Its
        ``integrated_server`` attribute contains the authoritative server Engine.
        """
        plan = self.create_export_plan(ExportType.CLIENT)
        server_package = plan.package_for(RuntimeRealm.SERVER)
        client_package = plan.package_for(RuntimeRealm.CLIENT)

        server_engine = Engine(
            data_model=server_package.data_model,
            renderer=NullRenderer(),
            realm=RuntimeRealm.SERVER,
        )
        client_engine = Engine(
            data_model=client_package.data_model,
            renderer=self.renderer.clone_for_runtime(),
            realm=RuntimeRealm.CLIENT,
        )
        client_engine.integrated_server = server_engine
        return client_engine
