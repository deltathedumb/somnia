"""Project-level helpers built from ordinary Somnia objects."""

from __future__ import annotations

from .model import DataModel
from .runtime import Engine


def create_project_data_model(name="Game"):
    """Create a DataModel with Somnia's required foundation services."""
    engine = Engine(DataModel(name=name))
    return engine.data_model
