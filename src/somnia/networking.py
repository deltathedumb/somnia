"""Transport primitives shared by integrated and remote Somnia networking."""

from __future__ import annotations


class NetworkPacket:
    """One realm-to-realm message carried by a network transport."""

    def __init__(self, channel, payload=None, sender=""):
        self.channel = str(channel)
        self.payload = payload
        self.sender = str(sender)

    def to_dict(self):
        return {
            "channel": self.channel,
            "payload": self.payload,
            "sender": self.sender,
        }


class TransportEndpoint:
    """Minimal transport interface consumed by NetworkProvider."""

    backend_name = "base"

    @property
    def connected(self):
        return False

    def send(self, packet):
        raise NotImplementedError

    def receive(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError


class LocalTransportEndpoint(TransportEndpoint):
    """In-memory endpoint using the same packet boundary as remote transports."""

    backend_name = "local"

    def __init__(self, role):
        self.role = str(role)
        self._peer = None
        self._inbox = []
        self._closed = False

    @property
    def connected(self):
        return (
            not self._closed
            and self._peer is not None
            and not self._peer._closed
        )

    def connect_peer(self, peer):
        if peer is self:
            raise ValueError("a transport endpoint cannot connect to itself")
        self._peer = peer
        return self

    def send(self, packet):
        if not self.connected:
            raise ConnectionError("local Somnia transport is not connected")
        if not isinstance(packet, NetworkPacket):
            raise TypeError("transport payload must be a NetworkPacket")
        self._peer._inbox.append(packet)
        return packet

    def receive(self):
        packets = list(self._inbox)
        self._inbox = []
        return packets

    def close(self):
        self._closed = True
        self._inbox = []


def create_local_transport_pair():
    """Return connected `(server, client)` in-memory endpoints."""
    server = LocalTransportEndpoint("server")
    client = LocalTransportEndpoint("client")
    server.connect_peer(client)
    client.connect_peer(server)
    return server, client
