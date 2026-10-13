import pytest

from gridworld.controllers.controller import Controller
from gridworld.engine import Engine
from gridworld.models.level import Level
from helpers import RecordingRenderer, ScriptedInput


@pytest.fixture
def level_data():
    # 5x3 level: start on the left, exit on the right
    return {
        "id": "test",
        "grid": [
            "#####",
            "#...#",
            "#####",
        ],
        "start": {"x": 1, "y": 1},
        "exit": {"x": 3, "y": 1},
    }


@pytest.fixture
def level(level_data):
    return Level(level_data)


@pytest.fixture
def renderer():
    return RecordingRenderer()


@pytest.fixture
def make_game(level, renderer):
    # Factory: each test gives its own keys, e.g. make_game(["d", "d"])
    def _make_game(keys=()):
        return Engine(level, Controller(ScriptedInput(keys)), renderer)
    return _make_game


@pytest.fixture
def game(make_game):
    # Fresh game with no scripted keys (for tests that call apply_action directly)
    return make_game()
