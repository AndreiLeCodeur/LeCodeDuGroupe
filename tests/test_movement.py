import pytest
from gridworld.engine import Engine
from gridworld.models.level import Level


class DummyController:
    def get_action(self):
        return "wait"

class DummyRenderer:
    def start(self): pass
    def update_render(self, state): pass
    def close(self): pass

def test_movement_and_turns():
    level = Level.load("levels/n0.json")
    engine = Engine(level, DummyController(), DummyRenderer())

    initial_turn = engine.turn
    engine.apply_action("east")  # Action de déplacement valide
    assert engine.turn == initial_turn + 1

def test_blocked_movement_consumes_turn():
    level = Level.load("levels/n0.json")
    engine = Engine(level, DummyController(), DummyRenderer())
    initial_turn = engine.turn

    # Tenter de traverser un mur (ex: "north" depuis la position initiale (1,1) si (1,0) est un mur)
    engine.apply_action("north")
    assert engine.turn == initial_turn + 1  # Le tour est consommé même en cas de blocage

def test_wait_action():
    level = Level.load("levels/n0.json")
    engine = Engine(level, DummyController(), DummyRenderer())
    initial_turn = engine.turn

    engine.apply_action("wait")
    assert engine.turn == initial_turn + 1

def test_unsupported_action_raises_error():
    level = Level.load("levels/n0.json")
    engine = Engine(level, DummyController(), DummyRenderer())
    with pytest.raises(ValueError):
        engine.apply_action("invalid_action") # type: ignore