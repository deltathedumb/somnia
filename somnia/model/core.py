"""Somnia's shared editor/runtime object model.

The hierarchy in this module is the hierarchy presented by the editor and used
by the running game. Serialization, property inspection, custom object types,
and future replication all build on the same objects and metadata.
"""

from __future__ import annotations

import uuid

from somnia.math import Quaternion, Transform, Vec3


def _copy_value(value):
    if isinstance(value, Vec3):
        return value.copy()
    if isinstance(value, Quaternion):
        return value.copy()
    if isinstance(value, Transform):
        return value.copy()
    if isinstance(value, list):
        return [_copy_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _copy_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(_copy_value(item) for item in value)
    return value


def serialize_value(value):
    """Convert a reflected property value to SEM-compatible data."""
    if isinstance(value, Vec3):
        return value.to_list()
    if isinstance(value, Quaternion):
        return value.to_list()
    if isinstance(value, Transform):
        return value.to_dict()
    if isinstance(value, list):
        return [serialize_value(item) for item in value]
    if isinstance(value, tuple):
        return [serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): serialize_value(item) for key, item in value.items()}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(
        "value of type " + type(value).__name__ + " is not SEM-serializable"
    )


def _coerce_value(value_type, value):
    if value_type is None or value is None:
        return value
    if value_type is Vec3:
        return Vec3.from_value(value)
    if value_type is Quaternion:
        return Quaternion.from_value(value)
    if value_type is Transform:
        return Transform.from_value(value)
    if value_type is float and isinstance(value, (int, float)):
        return float(value)
    if value_type is int and isinstance(value, int) and not isinstance(value, bool):
        return value
    if value_type is bool and isinstance(value, bool):
        return value
    if value_type is str and isinstance(value, str):
        return value
    if value_type is list and isinstance(value, list):
        return value
    if value_type is dict and isinstance(value, dict):
        return value
    if isinstance(value, value_type):
        return value
    raise TypeError(
        "expected " + value_type.__name__ + ", got " + type(value).__name__
    )


class Signal:
    """Small shared event primitive used by editor and runtime objects."""

    def __init__(self):
        self._listeners = []

    def connect(self, callback):
        if callback not in self._listeners:
            self._listeners.append(callback)
        return callback

    def disconnect(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def emit(self, *args):
        for callback in list(self._listeners):
            callback(*args)


class Property:
    """Reflected property shared by runtime, editor, and serializers."""

    def __init__(
        self,
        default=None,
        *,
        value_type=None,
        serializable=True,
        editor_visible=True,
        category="General",
        minimum=None,
        maximum=None,
        read_only=False,
    ):
        self.default = default
        self.value_type = value_type
        self.serializable = serializable
        self.editor_visible = editor_visible
        self.category = category
        self.minimum = minimum
        self.maximum = maximum
        self.read_only = read_only
        self.name = ""

    def __set_name__(self, owner, name):
        self.name = name

    def default_value(self):
        return _copy_value(self.default)

    def coerce(self, value):
        converted = _coerce_value(self.value_type, value)
        if self.minimum is not None and converted < self.minimum:
            raise ValueError(self.name + " must be >= " + str(self.minimum))
        if self.maximum is not None and converted > self.maximum:
            raise ValueError(self.name + " must be <= " + str(self.maximum))
        return converted

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return instance._property_values[self.name]

    def __set__(self, instance, value):
        if self.read_only and not instance._loading:
            raise AttributeError("property " + repr(self.name) + " is read-only")
        converted = self.coerce(value)
        old_value = instance._property_values.get(self.name)
        instance._property_values[self.name] = converted
        if old_value != converted:
            instance.property_changed.emit(instance, self.name, old_value, converted)

    def describe(self):
        return {
            "name": self.name,
            "type": self.value_type.__name__ if self.value_type is not None else "any",
            "category": self.category,
            "serializable": self.serializable,
            "editor_visible": self.editor_visible,
            "read_only": self.read_only,
            "minimum": self.minimum,
            "maximum": self.maximum,
        }


class ObjectMeta(type):
    """Collect reflected properties once for every object class."""

    def __new__(mcls, name, bases, namespace):
        properties = {}
        for base in bases:
            properties.update(getattr(base, "__somnia_properties__", {}))
        for key, value in namespace.items():
            if isinstance(value, Property):
                properties[key] = value
        cls = super().__new__(mcls, name, bases, namespace)
        cls.__somnia_properties__ = properties
        return cls


class ObjectRegistry:
    """Stable mapping between serialized type names and Python classes."""

    def __init__(self):
        self._types = {}
        self._names = {}

    def register(self, type_name, cls):
        if not isinstance(type_name, str) or not type_name:
            raise ValueError("object type name must be a non-empty string")
        existing = self._types.get(type_name)
        if existing is not None and existing is not cls:
            raise ValueError("object type already registered: " + type_name)
        self._types[type_name] = cls
        self._names[cls] = type_name
        cls.__somnia_type__ = type_name
        return cls

    def type_name(self, value_or_class):
        cls = value_or_class if isinstance(value_or_class, type) else type(value_or_class)
        return self._names.get(cls, getattr(cls, "__somnia_type__", cls.__name__))

    def resolve(self, type_name):
        return self._types.get(type_name)

    def create(self, type_name, object_id=None, name=None):
        cls = self.resolve(type_name)
        if cls is None:
            return UnknownObject(
                object_id=object_id,
                name=name or "Unknown Object",
                original_type=type_name,
            )
        return cls(object_id=object_id, name=name)

    def describe(self):
        return {
            type_name: cls.describe_class()
            for type_name, cls in sorted(self._types.items())
        }


OBJECT_TYPES = ObjectRegistry()


def register_object_class(type_name, registry=OBJECT_TYPES):
    """Register a project, plugin, editor, or engine object class."""

    def decorate(cls):
        registry.register(type_name, cls)
        return cls

    return decorate


class SomniaObject(metaclass=ObjectMeta):
    """Universal object used by both the editor and the running game."""

    name = Property("Object", value_type=str, category="Identity")
    enabled = Property(True, value_type=bool, category="Behavior")
    archivable = Property(True, value_type=bool, category="Behavior")

    def __init__(self, object_id=None, name=None):
        self.object_id = object_id or uuid.uuid4().hex
        self.parent = None
        self.children = []
        self.tags = []
        self.extensions = {}
        self.property_changed = Signal()
        self.child_added = Signal()
        self.child_removed = Signal()
        self.ancestry_changed = Signal()
        self._property_values = {}
        self._loading = True
        for property_name, descriptor in self.reflected_properties().items():
            self._property_values[property_name] = descriptor.default_value()
        if name is not None:
            self.name = name
        self._loading = False

    @classmethod
    def reflected_properties(cls):
        return dict(cls.__somnia_properties__)

    @classmethod
    def describe_class(cls):
        return {
            "type": getattr(cls, "__somnia_type__", cls.__name__),
            "class": cls.__name__,
            "properties": [
                descriptor.describe()
                for descriptor in cls.reflected_properties().values()
            ],
        }

    @property
    def type_name(self):
        return OBJECT_TYPES.type_name(self)

    def set_parent(self, parent, index=None):
        if parent is self:
            raise ValueError("an object cannot parent itself")
        ancestor = parent
        while ancestor is not None:
            if ancestor is self:
                raise ValueError("parenting would create a hierarchy cycle")
            ancestor = ancestor.parent

        old_parent = self.parent
        if old_parent is parent:
            if parent is not None and index is not None:
                parent.children.remove(self)
                parent.children.insert(index, self)
            return

        if old_parent is not None:
            old_parent.children.remove(self)
            old_parent.child_removed.emit(old_parent, self)

        self.parent = parent
        if parent is not None:
            if index is None:
                parent.children.append(self)
            else:
                parent.children.insert(index, self)
            parent.child_added.emit(parent, self)
        self.ancestry_changed.emit(self, old_parent, parent)

    def add_child(self, child, index=None):
        child.set_parent(self, index=index)
        return child

    def remove_child(self, child):
        if child.parent is not self:
            raise ValueError("object is not a child of this parent")
        child.set_parent(None)
        return child

    def walk(self, include_self=True):
        if include_self:
            yield self
        for child in list(self.children):
            yield from child.walk(include_self=True)

    def find_first(self, name, recursive=True):
        for child in self.children:
            if child.name == name:
                return child
            if recursive:
                found = child.find_first(name, recursive=True)
                if found is not None:
                    return found
        return None

    def get_path(self):
        names = [self.name]
        node = self.parent
        while node is not None:
            names.append(node.name)
            node = node.parent
        names.reverse()
        return "/".join(names)

    def add_tag(self, tag):
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag):
        if tag in self.tags:
            self.tags.remove(tag)

    def has_tag(self, tag):
        return tag in self.tags

    def serializable_properties(self):
        values = {}
        for name, descriptor in self.reflected_properties().items():
            if descriptor.serializable:
                values[name] = serialize_value(getattr(self, name))
        return values

    def apply_serialized_properties(self, values):
        self._loading = True
        try:
            descriptors = self.reflected_properties()
            for name, value in values.items():
                descriptor = descriptors.get(name)
                if descriptor is None:
                    self.extensions.setdefault("unknown_properties", {})[name] = value
                else:
                    setattr(self, name, value)
        finally:
            self._loading = False

    def clone(self, registry=OBJECT_TYPES):
        clone = registry.create(self.type_name, name=self.name)
        clone.tags = list(self.tags)
        clone.extensions = _copy_value(self.extensions)
        clone.apply_serialized_properties(self.serializable_properties())
        for child in self.children:
            clone.add_child(child.clone(registry=registry))
        return clone

    def __repr__(self):
        return "<" + self.type_name + " " + repr(self.name) + " " + self.object_id + ">"


@register_object_class("somnia.UnknownObject")
class UnknownObject(SomniaObject):
    """Preserves an unavailable custom type without corrupting the model."""

    original_type = Property("", value_type=str, category="Compatibility")
    raw_properties = Property({}, value_type=dict, category="Compatibility")

    def __init__(self, object_id=None, name=None, original_type=""):
        super().__init__(object_id=object_id, name=name)
        self.original_type = original_type

    @property
    def type_name(self):
        return self.original_type or "somnia.UnknownObject"

    def serializable_properties(self):
        values = dict(self.raw_properties)
        known = super().serializable_properties()
        known.pop("original_type", None)
        known.pop("raw_properties", None)
        values.update(known)
        return values

    def apply_serialized_properties(self, values):
        known_names = set(self.reflected_properties())
        known_values = {}
        raw_values = {}
        for name, value in values.items():
            if name in known_names and name not in ("original_type", "raw_properties"):
                known_values[name] = value
            else:
                raw_values[name] = value
        self.raw_properties = raw_values
        super().apply_serialized_properties(known_values)


@register_object_class("somnia.Folder")
class Folder(SomniaObject):
    pass


@register_object_class("somnia.ModelNode")
class ModelNode(SomniaObject):
    transform = Property(
        Transform.identity(),
        value_type=Transform,
        category="Transform",
    )


@register_object_class("somnia.Model")
class Model(ModelNode):
    """A transformable group of objects."""

    primary_object_id = Property("", value_type=str, category="Model")


@register_object_class("somnia.Service")
class Service(SomniaObject):
    """Base class for singleton systems inside a DataModel."""

    archivable = Property(False, value_type=bool, category="Behavior")


@register_object_class("somnia.DataModel")
class DataModel(SomniaObject):
    """Root of an editor or runtime object universe."""

    def __init__(self, object_id=None, name=None):
        super().__init__(object_id=object_id, name=name or "DataModel")

    def get_service(self, service_type):
        for child in self.children:
            if isinstance(child, service_type):
                return child
        return None

    def ensure_service(self, service_type, name=None):
        existing = self.get_service(service_type)
        if existing is not None:
            return existing
        service = service_type(name=name)
        self.add_child(service)
        return service


UnknownModelNode = UnknownObject
