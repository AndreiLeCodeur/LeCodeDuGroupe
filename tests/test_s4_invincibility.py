import pytest

from gridworld.s4.invincibility import Invincibility


def test_effect_counts_phases_and_stops_at_zero():
    effect = Invincibility()
    assert effect.remaining == 0
    effect.activate(5)
    assert effect.remaining == 5
    for remaining in [4, 3, 2, 1, 0, 0]:
        effect.tick()
        assert effect.remaining == remaining


def test_default_duration_is_five():
    effect = Invincibility()
    effect.activate()
    assert effect.remaining == 5


def test_tick_on_fresh_effect_stays_at_zero():
    effect = Invincibility()
    effect.tick()
    assert effect.remaining == 0


def test_activate_replaces_duration_instead_of_adding():
    effect = Invincibility()
    effect.activate(5)
    effect.tick()
    effect.activate(5)
    assert effect.remaining == 5
    effect.activate(3)
    assert effect.remaining == 3


def test_negative_duration_is_rejected_and_keeps_state():
    effect = Invincibility()
    effect.activate(4)
    with pytest.raises(ValueError):
        effect.activate(-1)
    assert effect.remaining == 4

