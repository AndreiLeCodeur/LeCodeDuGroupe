import pytest
from pathlib import Path
from unittest.mock import MagicMock

from gridworld.controllers.controller import Controller
from gridworld.engine import Engine
from gridworld.models.level import Level


@pytest.fixture
def level_fixture():
    # Charge le niveau n0 (7x5, départ (1,1), sortie (5,1))
    level_path = Path(__file__).parent.parent.parent / "levels" / "n0.json"
    return Level.load(level_path)


@pytest.fixture
def game_engine(level_fixture):
    # Moteur réel sur n0 ; les tests appellent apply_action directement
    return Engine(level_fixture, Controller(MagicMock()), MagicMock())


@pytest.fixture
def game_engine_near_wall(game_engine):
    # Sur n0, le départ (1,1) touche un mur au nord (1,0) et à l'ouest (0,1)
    assert not game_engine.level.is_walkable(1, 0)
    return game_engine


@pytest.fixture
def game_engine_on_edge():
    # Niveau sans mur de bordure : le joueur démarre au bord de la grille
    level = Level({"id": "edge", "grid": ["..."], "start": {"x": 0, "y": 0}, "exit": {"x": 2, "y": 0}})
    return Engine(level, Controller(MagicMock()), MagicMock())
