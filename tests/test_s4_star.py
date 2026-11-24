from gridworld.s4.star import Star
from testing.s4_fakes import FakeWorld, FixedRandom


def test_hidden_star_returns_but_collected_star_does_not():
    star = Star("star-1", 2, 2)
    world, rng = FakeWorld(), FixedRandom(0.25)
    star.update(world, rng)
    assert star.to_state() is None
    assert star.collect() is False
    star.update(world, rng)
    assert star.to_state()["appearance"] == "star"
    assert star.collect() is True
    star.update(world, rng)
    assert star.to_state() is None
    assert star.collect() is False


def test_initial_state_and_kind():
    star = Star("star-1", 2, 3)
    assert star.kind == "star"
    assert star.get_position() == (2, 3)
    assert star.to_state()["appearance"] == "star"


def test_to_state_returns_a_new_dictionary():
    star = Star("star-1", 2, 2)
    first = star.to_state()
    first["appearance"] = "changed"
    assert star.to_state()["appearance"] == "star"
    assert star.to_state() is not star.to_state()


def test_low_value_toggles_visibility():
    star = Star("star-1", 2, 2)
    star.update(FakeWorld(), FixedRandom(0.25))
    assert star.to_state() is None


def test_high_value_keeps_visibility():
    star = Star("star-1", 2, 2)
    star.update(FakeWorld(), FixedRandom(0.75))
    assert star.to_state() is not None


def test_boundary_value_does_not_toggle():
    star = Star("star-1", 2, 2)
    star.update(FakeWorld(), FixedRandom(0.5))
    assert star.to_state() is not None


def test_two_low_updates_hide_then_show_again():
    star = Star("star-1", 2, 2)
    world, rng = FakeWorld(), FixedRandom(0.25)
    star.update(world, rng)
    assert star.to_state() is None
    star.update(world, rng)
    assert star.to_state() is not None


def test_star_does_not_move():
    star = Star("star-1", 2, 2)
    for _ in range(3):
        star.update(FakeWorld(), FixedRandom(0.25))
    assert star.get_position() == (2, 2)


def test_collect_succeeds_only_once():
    star = Star("star-1", 2, 2)
    assert star.collect() is True
    assert star.collect() is False


def test_collected_star_never_reappears():
    star = Star("star-1", 2, 2)
    star.collect()
    for _ in range(4):
        star.update(FakeWorld(), FixedRandom(0.25))
        assert star.to_state() is None
        assert star.collect() is False


def test_stars_have_independent_state():
    first = Star("star-1", 1, 1)
    second = Star("star-2", 3, 3)
    assert first.collect() is True
    assert second.to_state() is not None
    assert second.collect() is True


def test_star_exposes_id_and_kind():
    star = Star("star-1", 2, 3)
    assert star.id == "star-1"
    assert star.to_state()["id"] == "star-1"