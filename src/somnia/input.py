"""Backend-neutral deterministic input frames and test backends."""

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
        self.position = _pointer_value(position)
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

    def to_dict(self):
        result = {
            "type": self.event_type,
            "code": self.code,
            "value": self.value,
            "device": self.device,
        }
        if self.position:
            result["position"] = list(self.position)
        if self.text:
            result["text"] = self.text
        return result


def _pointer_value(value):
    if value is None:
        return []
    values = list(value)
    if not values:
        return []
    if len(values) != 2:
        raise ValueError("pointer positions require exactly two values")
    return [float(values[0]), float(values[1])]


def _axis_values(values):
    result = {}
    for code, value in dict(values or {}).items():
        result[str(code)] = float(value)
    return {code: result[code] for code in sorted(result)}


class InputFrame:
    """A complete, deterministic input snapshot for one engine frame."""

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
        self.held_inputs = sorted({str(code) for code in list(held_inputs or [])})
        self.axes = _axis_values(axes)
        self.pointer = _pointer_value(pointer)
        self.wheel_delta = float(wheel_delta)
        self.text = str(text)

    @classmethod
    def empty(cls, frame_number=0):
        return cls(frame_number=frame_number)

    def to_dict(self):
        return {
            "frame_number": self.frame_number,
            "events": [event.to_dict() for event in self.events],
            "held_inputs": list(self.held_inputs),
            "axes": dict(self.axes),
            "pointer": list(self.pointer),
            "wheel_delta": self.wheel_delta,
            "text": self.text,
        }


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


class QueueInputBackend(InputBackend):
    """Deterministic input source for tests, replays, and editor injection."""

    backend_name = "queue"

    def __init__(self, frames=None):
        self._queued = []
        self._held = set()
        self._axes = {}
        self._pointer = []
        for frame in list(frames or []):
            if isinstance(frame, InputFrame):
                self.submit_frame(frame)
            elif isinstance(frame, dict):
                payload = dict(frame)
                payload.pop("frame_number", None)
                self.submit(**payload)
            else:
                raise TypeError("queued input frames must be InputFrame objects or dictionaries")

    def submit(
        self,
        events=None,
        held_inputs=None,
        axes=None,
        pointer=None,
        wheel_delta=0.0,
        text="",
    ):
        self._queued.append(
            {
                "events": [InputEvent.from_value(event) for event in list(events or [])],
                "held_inputs": None if held_inputs is None else list(held_inputs),
                "axes": None if axes is None else dict(axes),
                "pointer": None if pointer is None else list(pointer),
                "wheel_delta": float(wheel_delta),
                "text": str(text),
            }
        )
        return self

    def submit_frame(self, frame):
        return self.submit(
            events=frame.events,
            held_inputs=frame.held_inputs,
            axes=frame.axes,
            pointer=frame.pointer,
            wheel_delta=frame.wheel_delta,
            text=frame.text,
        )

    def poll(self, frame_number):
        if not self._queued:
            return InputFrame(
                frame_number=frame_number,
                held_inputs=self._held,
                axes=self._axes,
                pointer=self._pointer,
            )

        payload = self._queued.pop(0)
        events = payload["events"]
        frame_text = payload["text"]
        wheel_delta = payload["wheel_delta"]

        for event in events:
            if event.event_type == InputEventType.BUTTON_DOWN:
                self._held.add(event.code)
            elif event.event_type == InputEventType.BUTTON_UP:
                self._held.discard(event.code)
            elif event.event_type == InputEventType.AXIS:
                self._axes[event.code] = event.value
            elif event.event_type == InputEventType.POINTER:
                self._pointer = list(event.position)
            elif event.event_type == InputEventType.WHEEL:
                wheel_delta += event.value
            elif event.event_type == InputEventType.TEXT:
                frame_text += event.text

        if payload["held_inputs"] is not None:
            self._held = {str(code) for code in payload["held_inputs"]}
        if payload["axes"] is not None:
            self._axes = _axis_values(payload["axes"])
        if payload["pointer"] is not None:
            self._pointer = _pointer_value(payload["pointer"])

        return InputFrame(
            frame_number=frame_number,
            events=events,
            held_inputs=self._held,
            axes=self._axes,
            pointer=self._pointer,
            wheel_delta=wheel_delta,
            text=frame_text,
        )

    def clone_for_runtime(self):
        return QueueInputBackend()
