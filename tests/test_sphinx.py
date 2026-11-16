import json
from pathlib import Path

import pytest

from gridworld.controllers.controller import Controller
from gridworld.engine import Engine
from gridworld.models.level import Level, LevelError
from helpers import ScriptedInput

LEVELS = Path(__file__).parent.parent / "levels"

SPHINX_ENTITY = {"id": "sphinx-1", "kind": "sphinx", "x": 5, "y": 1, "appearance": "sphinx"}


@pytest.fixture
def sphinx_level():
    return Level.load(LEVELS / "sphinx.json")


def make_engine(level, renderer):
    return Engine(level, Controller(ScriptedInput([])), renderer)


# --- Level.get_sphinx ---
def test_sphinx_map_returns_entity_on_exit(sphinx_level):
    assert sphinx_level.exit_pos == (5, 1)
    assert sphinx_level.sphinx_position == sphinx_level.exit_pos
    assert sphinx_level.get_sphinx() == SPHINX_ENTITY


def test_n0_has_no_sphinx():
    level = Level.load(LEVELS / "n0.json")
    assert level.sphinx_position is None
    assert level.get_sphinx() is None


def test_sphinx_false_means_no_sphinx(level_data):
    level_data["sphinx"] = False
    assert Level(level_data).get_sphinx() is None


def test_sphinx_follows_the_exit(level_data):
    # pas de seconde paire de coordonnées : le sphinx est là où est la sortie
    level_data["sphinx"] = True
    sphinx = Level(level_data).get_sphinx()
    assert (sphinx["x"], sphinx["y"]) == (3, 1)


def test_sphinx_marker_must_be_boolean(level_data):
    level_data["sphinx"] = "true"
    with pytest.raises(LevelError):
        Level(level_data)


def test_exit_stays_an_exit_under_the_sphinx(sphinx_level):
    assert sphinx_level.is_exit(5, 1)
    assert sphinx_level.to_state()["tiles"][1][5] == "exit"


def test_sphinx_map_stores_no_riddle():
    # l'énigme sera inventée par le LLM en S2-03 : rien de privé dans la carte
    data = json.loads((LEVELS / "sphinx.json").read_text(encoding="utf-8"))
    assert set(data) == {"id", "grid", "start", "exit", "sphinx"}
    assert data["sphinx"] is True


# --- Engine.get_state ---
def test_state_lists_player_then_sphinx(sphinx_level, renderer):
    state = make_engine(sphinx_level, renderer).get_state()
    assert [e["id"] for e in state["entities"]] == ["player-1", "sphinx-1"]
    assert state["entities"][1] == SPHINX_ENTITY
    assert set(state) == {"level", "entities", "player_id", "status", "turn",
                          "message", "interaction", "extras"}
    json.dumps(state)


def test_state_without_sphinx_only_lists_player(game):
    state = game.get_state()
    assert [e["kind"] for e in state["entities"]] == ["player"]


def test_sphinx_entity_does_not_follow_the_player(sphinx_level, renderer):
    engine = make_engine(sphinx_level, renderer)
    engine.apply_action("east")
    entities = engine.get_state()["entities"]
    assert (entities[0]["x"], entities[0]["y"]) == (2, 1)
    assert entities[1] == SPHINX_ENTITY


def test_state_copy_cannot_move_the_sphinx(sphinx_level, renderer):
    engine = make_engine(sphinx_level, renderer)
    engine.get_state()["entities"][1]["x"] = 0
    assert engine.get_state()["entities"][1] == SPHINX_ENTITY
