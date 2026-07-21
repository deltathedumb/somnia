"""Input helpers for tests, editor injection, replays, and serialization."""

from __future__ import annotations

from .input_core import (
    InputBackend,
    InputEvent,
    InputEventType,
    InputFrame,
    NullInputBackend,
    pointer_value,
)


def input_event_to_dict(event):
    event = InputEvent.from_value(event)
    result = {
        "type": event.event_type,
        "code": event.code,
        "value": event.value,
        "device": event.device,
    }
    if event.position:
        result["position"] = list(event.position)
    if event.text:
        result["text"] = event.text
    return result


def input_frame_to_dict(frame):
    return {
        "frame_number": frame.frame_number,
        "events": [input_event_to_dict(event) for event in frame.events],
        "held_inputs": list(frame.held_inputs),
        "axes": dict(frame.axes),
        "pointer": list(frame.pointer),
        "wheel_delta": frame.wheel_delta,
        "text": frame.text,
    }


def _axis_values(values):
    result = {}
    for code, value in dict(values or {}).items():
        result[str(code)] = float(value)
    return {code: result[code] for code in sorted(result)}


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
            self._pointer = pointer_value(payload["pointer"])

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


__all__ = [
    "InputBackend",
    "InputEvent",
    "InputEventType",
    "InputFrame",
    "NullInputBackend",
    "QueueInputBackend",
    "input_event_to_dict",
    "input_frame_to_dict",
]
