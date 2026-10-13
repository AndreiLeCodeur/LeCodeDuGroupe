import pytest

from gridworld.contracts import InputSource, Renderer
from helpers import RecordingRenderer, ScriptedInput


def test_level_fixture(level):
    assert level.get_start() == (1, 1)
    assert level.is_exit(3, 1)
    assert not level.is_walkable(0, 0)


def test_game_starts_fresh(game):
    assert game.player.get_position() == (1, 1)
    assert game.status == "playing"
    assert game.turn == 0


def test_moving_does_not_leak_into_next_test(game):
    # Same expectations as test_game_starts_fresh after a move:
    # if state were shared, one of the two tests would fail.
    game.apply_action("east")
    assert game.player.get_position() == (2, 1)
    assert game.turn == 1


def test_level_data_is_a_new_dict(level_data):
    level_data["id"] = "changed"
    assert level_data["id"] == "changed"


def test_level_data_is_not_changed_by_other_tests(level_data):
    assert level_data["id"] == "test"


def test_scripted_game_reaches_exit(make_game, renderer):
    game = make_game(["d", "d"])
    game.run()
    assert game.status == "won"
    # initial state + one state per move
    assert [state["turn"] for state in renderer.states] == [0, 1, 2]
    assert renderer.states[-1]["status"] == "won"


def test_scripted_input_returns_keys_in_order():
    source = ScriptedInput(["z", "d"])
    assert source.read_key() == "z"
    assert source.read_key() == "d"
    assert source.reads == 2


def test_scripted_input_fails_when_exhausted(make_game):
    # Only one key: the game is not over, so the engine asks for another one.
    game = make_game(["d"])
    with pytest.raises(AssertionError, match="exhausted"):
        game.run()


def test_renderer_stores_snapshots(game, renderer):
    game.render(game.get_state())
    game.apply_action("east")
    game.render(game.get_state())
    # The first snapshot must not change when the game moves on.
    assert renderer.states[0]["entities"][0]["x"] == 1
    assert renderer.states[1]["entities"][0]["x"] == 2


def test_doubles_follow_contracts():
    # Protocols are structural: check the required methods exist.
    for name in ("read_key",):
        assert callable(getattr(ScriptedInput([]), name))
    for name in ("start", "update_render", "close"):
        assert callable(getattr(RecordingRenderer(), name))
    source: InputSource = ScriptedInput([])
    view: Renderer = RecordingRenderer()
    assert source is not None and view is not None
