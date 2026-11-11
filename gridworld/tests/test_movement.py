import pytest


@pytest.mark.parametrize("action, expected", [
    ("east", (2, 1)),
    ("south", (1, 2)),
])
def test_movements_from_start(game_engine, action, expected):
    # Déplacement sur sol libre depuis le départ (1,1) de n0
    initial_turn = game_engine.turn
    game_engine.apply_action(action)
    assert game_engine.player.get_position() == expected
    assert game_engine.turn == initial_turn + 1


def test_movements_in_four_directions(game_engine):
    # Depuis (2,2) les quatre voisins (2,1), (3,2)=mur, (2,3), (1,2) : on teste un aller-retour
    game_engine.player.move_to(2, 2)
    moves = [("north", (2, 1)), ("south", (2, 2)), ("west", (1, 2)), ("east", (2, 2))]
    for turn, (action, expected) in enumerate(moves, start=1):
        game_engine.apply_action(action)
        assert game_engine.player.get_position() == expected
        assert game_engine.turn == turn


@pytest.mark.parametrize("action", ["north", "west"])
def test_wall_collisions_consume_turn(game_engine_near_wall, action):
    # Se déplacer dans un mur doit bloquer le joueur mais compter 1 tour
    start_pos = game_engine_near_wall.player.get_position()
    turns_before = game_engine_near_wall.turn

    game_engine_near_wall.apply_action(action)

    assert game_engine_near_wall.player.get_position() == start_pos  # bloqué
    assert game_engine_near_wall.turn == turns_before + 1  # tour consommé


@pytest.mark.parametrize("action", ["north", "west", "south"])
def test_boundary_collisions_consume_turn(game_engine_on_edge, action):
    # Sortir de la grille doit bloquer le joueur mais compter 1 tour
    game_engine_on_edge.apply_action(action)
    assert game_engine_on_edge.player.get_position() == (0, 0)
    assert game_engine_on_edge.turn == 1


def test_wait_action_consumes_turn(game_engine):
    start_pos = game_engine.player.get_position()
    turns_before = game_engine.turn

    game_engine.apply_action("wait")

    assert game_engine.player.get_position() == start_pos
    assert game_engine.turn == turns_before + 1


def test_unsupported_action_raises_value_error(game_engine):
    state_before = game_engine.get_state()

    with pytest.raises(ValueError):
        game_engine.apply_action("dance")  # Action incorrecte

    # L'état du jeu ne doit pas avoir changé
    assert game_engine.get_state() == state_before


def test_reaching_exit_wins(game_engine):
    game_engine.player.move_to(4, 1)
    game_engine.apply_action("east")
    assert game_engine.player.get_position() == (5, 1)
    assert game_engine.status == "won"
