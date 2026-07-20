"""Undoable editor operations against the live Somnia object hierarchy."""

from __future__ import annotations


class Command:
    description = "Command"

    def execute(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError


class SetPropertyCommand(Command):
    def __init__(self, target, property_name, value):
        descriptors = target.reflected_properties()
        if property_name not in descriptors:
            raise AttributeError(
                target.type_name + " has no reflected property " + repr(property_name)
            )
        self.target = target
        self.property_name = property_name
        self.old_value = getattr(target, property_name)
        self.new_value = value
        self.description = "Set " + target.name + "." + property_name

    def execute(self):
        setattr(self.target, self.property_name, self.new_value)

    def undo(self):
        setattr(self.target, self.property_name, self.old_value)


class ReparentCommand(Command):
    def __init__(self, target, new_parent, new_index=None):
        self.target = target
        self.old_parent = target.parent
        self.old_index = (
            self.old_parent.children.index(target) if self.old_parent is not None else None
        )
        self.new_parent = new_parent
        self.new_index = new_index
        self.description = "Reparent " + target.name

    def execute(self):
        self.target.set_parent(self.new_parent, index=self.new_index)

    def undo(self):
        self.target.set_parent(self.old_parent, index=self.old_index)


class CreateObjectCommand(Command):
    def __init__(self, parent, obj, index=None):
        self.parent = parent
        self.obj = obj
        self.index = index
        self.description = "Create " + obj.name

    def execute(self):
        self.parent.add_child(self.obj, index=self.index)

    def undo(self):
        if self.obj.parent is self.parent:
            self.parent.remove_child(self.obj)


class DeleteObjectCommand(Command):
    def __init__(self, target):
        if target.parent is None:
            raise ValueError("cannot delete an unparented object through editor history")
        self.target = target
        self.parent = target.parent
        self.index = self.parent.children.index(target)
        self.description = "Delete " + target.name

    def execute(self):
        if self.target.parent is self.parent:
            self.parent.remove_child(self.target)

    def undo(self):
        self.parent.add_child(self.target, index=self.index)
