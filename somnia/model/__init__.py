"""Unified Somnia object hierarchy and reflection API."""

from .core import (
    DataModel,
    Folder,
    Model,
    ModelNode,
    OBJECT_TYPES,
    ObjectRegistry,
    Property,
    Service,
    Signal,
    SomniaObject,
    UnknownModelNode,
    UnknownObject,
    register_object_class,
    serialize_value,
)
from .document import ModelDocument

# Import built-in object classes for registration side effects.
from .native import NativeFunction, NativeLibrary, NativeLibraryService
from .scripting import PortaPyRuntime, PythonScript, ScriptService

__all__ = [
    "DataModel",
    "Folder",
    "Model",
    "ModelDocument",
    "ModelNode",
    "NativeFunction",
    "NativeLibrary",
    "NativeLibraryService",
    "OBJECT_TYPES",
    "ObjectRegistry",
    "PortaPyRuntime",
    "Property",
    "PythonScript",
    "ScriptService",
    "Service",
    "Signal",
    "SomniaObject",
    "UnknownModelNode",
    "UnknownObject",
    "register_object_class",
    "serialize_value",
]
