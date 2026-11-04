import pytest

def test_movements_in_four_directions(game_engine):
    # Tester UP, DOWN, LEFT, RIGHT sur sol libre
    initial_turns = game_engine.turns
    game_engine.step("RIGHT")
    assert game_engine.player.position == (expected_x, expected_y)
    assert game_engine.turns == initial_turns + 1

def test_wall_and_boundary_collisions_consume_turn(game_engine_near_wall):
    # Se déplacer dans un mur ou hors grille doit bloquer le joueur mais compter 1 tour
    start_pos = game_engine_near_wall.player.position
    turns_before = game_engine_near_wall.turns

    game_engine_near_wall.step("UP")  # Direction vers le mur

    assert game_engine_near_wall.player.position == start_pos  # bloqué
    assert game_engine_near_wall.turns == turns_before + 1    # tour perdu

def test_wait_action_consumes_turn(game_engine):
    start_pos = game_engine.player.position
    turns_before = game_engine.turns

    game_engine.step("WAIT")

    assert game_engine.player.position == start_pos
    assert game_engine.turns == turns_before + 1

def test_unsupported_action_raises_value_error(game_engine):
    start_pos = game_engine.player.position
    turns_before = game_engine.turns

    with pytest.raises(ValueError):
        game_engine.step("DANCE")  # Action incorrecte

    # L'état du jeu ne doit pas avoir changé
    assert game_engine.player.position == start_pos
    assert game_engine.turns == turns_before