import json

import pytest

from gridworld.s4.enemies import BaseEnemy, ChaserEnemy, HorizontalEnemy, VerticalEnemy
from testing.s4_fakes import FakeWorld, FixedRandom
from testing.s4_reference import legacy_trace

NEW_CLASSES = {"horizontal": HorizontalEnemy, "vertical": VerticalEnemy,
               "chaser": ChaserEnemy}


def run(actor, world, turns):
    rng = FixedRandom()
    states = []
    for _ in range(turns):
        actor.update(world, rng)
        states.append(actor.to_state())
    return states


# --- Supplied starting test -------------------------------------------------

def test_horizontal_preserves_the_supplied_behavior():
    expected = legacy_trace("horizontal", "h-1", 3, 2, FakeWorld(width=5), 5)
    actor = HorizontalEnemy("h-1", 3, 2)
    world, rng = FakeWorld(width=5), FixedRandom()
    actual = []
    for _ in range(5):
        actor.update(world, rng)
        actual.append(actor.to_state())
    assert actual == expected
    assert [state["x"] for state in actual] == [3, 2, 1, 1, 2]


# --- Shared structure -------------------------------------------------------

@pytest.mark.parametrize("cls", NEW_CLASSES.values())
def test_every_enemy_inherits_base_and_satisfies_turn_actor(cls):
    actor = cls("e-1", 2, 3)
    assert isinstance(actor, BaseEnemy)
    assert actor.id == "e-1"
    assert actor.kind == "enemy"
    assert actor.get_position() == (2, 3)
    for name in ("get_position", "update", "to_state"):
        assert callable(getattr(actor, name))


@pytest.mark.parametrize(("cls", "appearance"), [
    (HorizontalEnemy, "enemy.horizontal"),
    (VerticalEnemy, "enemy.vertical"),
    (ChaserEnemy, "enemy.chaser"),
])
def test_to_state_is_the_inherited_public_representation(cls, appearance):
    assert "to_state" not in cls.__dict__  # inherited, not duplicated
    state = cls("e-1", 4, 2).to_state()
    assert state == {"id": "e-1", "kind": "enemy", "x": 4, "y": 2,
                     "appearance": appearance}
    assert json.loads(json.dumps(state)) == state


def test_base_enemy_update_must_be_overridden():
    with pytest.raises(NotImplementedError):
        BaseEnemy("e-1", 1, 1).update(FakeWorld(), FixedRandom())


def test_modifying_a_state_does_not_move_the_enemy():
    actor = VerticalEnemy("v-1", 2, 2)
    state = actor.to_state()
    state["x"], state["y"] = 99, 99
    assert actor.get_position() == (2, 2)
    assert actor.to_state() is not state
    assert actor.to_state()["x"] == 2


def test_instances_are_independent():
    first, second = HorizontalEnemy("h-1", 3, 2), HorizontalEnemy("h-2", 1, 3)
    world = FakeWorld(width=5)
    first.update(world, FixedRandom())  # blocked: reverses only its own direction
    assert first.direction == -1
    assert second.direction == 1
    assert second.get_position() == (1, 3)


# --- Patrols ----------------------------------------------------------------

def test_horizontal_reverses_without_moving_then_returns():
    actor = HorizontalEnemy("h-1", 3, 2)
    world = FakeWorld(width=5)
    actor.update(world, FixedRandom())
    assert actor.get_position() == (3, 2)
    actor.update(world, FixedRandom())
    assert actor.get_position() == (2, 2)


def test_vertical_starts_south_and_reverses_on_obstacle():
    actor = VerticalEnemy("v-1", 2, 2)
    world = FakeWorld(blocked={(2, 4)})
    states = run(actor, world, 4)
    assert [s["y"] for s in states] == [3, 3, 2, 1]
    assert all(s["x"] == 2 for s in states)


def test_patrol_asks_the_world_before_moving():
    actor = HorizontalEnemy("h-1", 2, 2)
    world = FakeWorld()
    actor.update(world, FixedRandom())
    assert world.queries == [("h-1", 3, 2)]


# --- Chaser -----------------------------------------------------------------

def test_chaser_prefers_north_before_east_on_ties():
    actor = ChaserEnemy("c-1", 3, 4)
    actor.update(FakeWorld(player=(5, 2)), FixedRandom())
    assert actor.get_position() == (3, 3)


def test_chaser_takes_the_next_reducing_step_when_blocked():
    actor = ChaserEnemy("c-1", 3, 4)
    world = FakeWorld(player=(5, 2), blocked={(3, 3)})
    actor.update(world, FixedRandom())
    assert actor.get_position() == (4, 4)
    assert world.queries == [("c-1", 3, 3), ("c-1", 4, 4)]


def test_chaser_waits_when_no_step_reduces_the_distance():
    actor = ChaserEnemy("c-1", 3, 2)
    world = FakeWorld(player=(3, 5), blocked={(3, 3)})
    actor.update(world, FixedRandom())
    assert actor.get_position() == (3, 2)


def test_chaser_waits_on_the_player_cell():
    actor = ChaserEnemy("c-1", 2, 2)
    world = FakeWorld(player=(2, 2))
    actor.update(world, FixedRandom())
    assert actor.get_position() == (2, 2)
    assert world.queries == []


# --- Old/new traces over several turns --------------------------------------

@pytest.mark.parametrize(("kind", "x", "y", "world_args"), [
    ("horizontal", 1, 3, {"width": 6, "blocked": {(3, 3)}}),
    ("vertical", 4, 1, {"height": 6}),
    ("vertical", 2, 2, {"blocked": {(2, 4)}}),
    ("chaser", 7, 5, {"player": (1, 1), "blocked": {(7, 4), (5, 3)}}),
    ("chaser", 2, 5, {"player": (6, 1)}),
])
def test_new_enemies_match_the_legacy_trace(kind, x, y, world_args):
    expected = legacy_trace(kind, f"{kind}-1", x, y, FakeWorld(**world_args), 8)
    actual = run(NEW_CLASSES[kind](f"{kind}-1", x, y), FakeWorld(**world_args), 8)
    assert actual == expected
