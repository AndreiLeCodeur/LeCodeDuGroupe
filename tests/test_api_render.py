"""One complete GET test and one POST test to complete; no live server."""
import pytest
from gridworld.api_render import create_app
from gridworld.controllers.controller import Controller
from gridworld.controllers.terminal_input import TerminalInput
from gridworld.engine import Engine
from gridworld.models.level import Level
from gridworld.views.bash_render import BashRender


@pytest.fixture
def engine():
    level = Level({"id": "test", "grid": ["#####", "#...#", "#####"],
                   "start": {"x": 1, "y": 1}, "exit": {"x": 3, "y": 1}})
    return Engine(level, Controller(TerminalInput()), BashRender())


def test_get_does_not_advance_game(engine):
    client = create_app(engine).test_client()
    before = engine.get_state()
    first = client.get("/api/state")
    second = client.get("/api/state")
    assert first.status_code == 200
    assert first.get_json() == second.get_json()
    assert first.get_json()["state"] == before == engine.get_state()


def test_post_moves_player(engine):
    client = create_app(engine).test_client()
    response = client.post("/api/actions", json={"action": "east"})
    assert response.status_code == 200
    state = response.get_json()["state"]
    player = state["entities"][0]
    assert (player["x"], player["y"]) == (2, 1)
    assert state["turn"] == 1
    assert state["status"] == "playing"
    # The engine itself moved (not just the response), exactly once
    assert engine.get_state() == state
    # A following GET observes the same state without advancing it
    follow_up = client.get("/api/state")
    assert follow_up.status_code == 200
    assert follow_up.get_json()["state"] == state


def test_post_quit_closes_game(engine):
    client = create_app(engine).test_client()
    response = client.post("/api/actions", json={"action": "quit"})
    assert response.status_code == 200
    assert response.get_json()["running"] is False
    # Once closed, further actions are refused and the state is unchanged
    refused = client.post("/api/actions", json={"action": "east"})
    assert refused.status_code == 409
    assert refused.get_json()["error"]["code"] == "game_closed"
    assert engine.get_state()["turn"] == 0
