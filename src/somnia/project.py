"""Project-level helpers built from ordinary Somnia objects."""

from __future__ import annotations

from .model import Game, RuntimeRealm
from .runtime import Engine


def create_project_data_model(name="Game"):
    """Create a canonical authoring Game with every selected provider."""
    engine = Engine(Game(name=name, realm=RuntimeRealm.PROJECT))
    return engine.data_model
