"""Minimal backend-neutral input types used by the engine runtime."""

from __future__ import annotations


class InputEventType:
    BUTTON_DOWN = "button_down"
    BUTTON_UP = "button_up"
    AXIS = "axis"
    POINTER = "pointer"
    WHEEL = "wheel"
    TEXT = "text"

    @classmethod
    def normalize(cls, value):
        normalized = str(value).lower()
        supported = (
            cls.BUTTON_DOWN,
            cls.BUTTON_UP,
            cls.AXIS,
            cls.POINTER,
            cls.WHEEL,
            cls.TEXT,
        )
        if normalized not in supported:
            raise ValueError("unsupported Somnia input event type: " + normalized)
        return normalized


class InputEvent:
    """One normalized input transition inside an :class:`InputFrame`."""

    def __init__(
        self,
        event_type,
        code="",
        value=0.0,
        device="",
        position=None,
        text="",
    ):
        self.event_type = InputEventType.normalize(event_type)
        self.code = str(code)
        self.value = float(value)
        self.device = str(device)
        self.position = pointer_value(position)
        self.text = str(text)

    @classmethod
    def from_value(cls, value):
        if isinstance(value, cls):
            return value
        if not isinstance(value, dict):
            raise TypeError("input events must be InputEvent objects or dictionaries")
        return cls(
            value.get("type", value.get("event_type", "")),
            code=value.get("code", ""),
            value=value.get("value", 0.0),
            device=value.get("device", ""),
            position=value.get("position"),
            text=value.get("text", ""),
        )


def pointer_value(value):
    if value is None:
        return []
    values = list(value)
    if not values:
        return []
    if len(values) != 2:
        raise ValueError("pointer positions require exactly two values")
    return [float(values[0]), float(values[1])]


class InputFrame:
    """A complete input snapshot for one deterministic engine frame."""

    def __init__(
        self,
        frame_number=0,
        events=None,
        held_inputs=None,
        axes=None,
        pointer=None,
        wheel_delta=0.0,
        text="",
    ):
        self.frame_number = int(frame_number)
        self.events = [InputEvent.from_value(event) for event in list(events or [])]
        self.held_inputs = sorted([str(code) for code in list(held_inputs or [])])
        self.axes = dict(axes or {})
        self.pointer = pointer_value(pointer)
        self.wheel_delta = float(wheel_delta)
        self.text = str(text)

    @classmethod
    def empty(cls, frame_number=0):
        return cls(frame_number=frame_number)


class InputBackend:
    """Interface implemented by native, editor, replay, and test input sources."""

    backend_name = "base"

    def initialize(self, data_model):
        return self

    def poll(self, frame_number):
        raise NotImplementedError

    def clone_for_runtime(self):
        return type(self)()

    def shutdown(self):
        return None


class NullInputBackend(InputBackend):
    backend_name = "null"

    def poll(self, frame_number):
        return InputFrame.empty(frame_number=frame_number)
