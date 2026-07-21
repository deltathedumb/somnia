"""Somnia engine host built around provider-based client/server DataModels."""

from __future__ import annotations

from somnia.build import ExportType, create_export_plan
from somnia.input_core import InputFrame, NullInputBackend
from somnia.model import (
    Game,
    InputProvider,
    NativeLibrary,
    NetworkProvider,
    RuntimeRealm,
    get_provider,
    install_canonical_providers,
)
from somnia.networking import create_local_transport_pair
from somnia.rendering import NullRenderer


class Engine:
    """Coordinate one logical Somnia runtime realm.

    A normal Client play/export creates a client Engine plus an invisible
    integrated server Engine. Both runtimes retain separate DataModels and
    communicate through NetworkProvider rather than shared object references.
    """

    def __init__(
        self,
        data_model=None,
        renderer=None,
        realm=RuntimeRealm.PROJECT,
        input_backend=None,
    ):
        normalized_realm = RuntimeRealm.normalize(realm)
        if data_model is None:
            data_model = Game(realm=normalized_realm)
        self.data_model = data_model
        self.realm = normalized_realm
        if isinstance(self.data_model, Game):
            self.data_model.realm = normalized_realm
        self.renderer = renderer or NullRenderer()
        self.input_backend = input_backend or NullInputBackend()
        self.input_frame = InputFrame.empty()
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
        self.input_backend.initialize(self.data_model)
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

    def poll_input(self):
        next_frame_number = self.frame_number + 1
        frame = self.input_backend.poll(next_frame_number)
        if not isinstance(frame, InputFrame):
            raise TypeError("input backends must return somnia.InputFrame objects")
        if frame.frame_number != next_frame_number:
            raise ValueError("input backend returned an unexpected frame number")
        self.input_frame = frame
        provider = self.get_provider(InputProvider, create=False)
        if provider is not None:
            provider.apply_frame(frame, backend_name=self.input_backend.backend_name)
        return frame

    def frame(self):
        if not self.initialized:
            self.initialize()
        self.poll_input()
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
        network = self.get_provider(NetworkProvider, create=False)
        if network is not None:
            network.close()
        self.input_backend.shutdown()
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
        Both NetworkProviders communicate through paired in-memory endpoints that
        preserve the same packet boundary expected from future remote transports.
        """
        plan = self.create_export_plan(ExportType.CLIENT)
        server_package = plan.package_for(RuntimeRealm.SERVER)
        client_package = plan.package_for(RuntimeRealm.CLIENT)

        server_engine = Engine(
            data_model=server_package.data_model,
            renderer=NullRenderer(),
            input_backend=NullInputBackend(),
            realm=RuntimeRealm.SERVER,
        )
        client_engine = Engine(
            data_model=client_package.data_model,
            renderer=self.renderer.clone_for_runtime(),
            input_backend=self.input_backend.clone_for_runtime(),
            realm=RuntimeRealm.CLIENT,
        )

        server_transport, client_transport = create_local_transport_pair()
        server_engine.get_provider(NetworkProvider).attach_transport(server_transport)
        client_engine.get_provider(NetworkProvider).attach_transport(client_transport)
        client_engine.integrated_server = server_engine
        return client_engine
