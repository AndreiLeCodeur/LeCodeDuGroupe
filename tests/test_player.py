import pytest
from gridworld.models.player import Player

def test_player_movement_independence():
    p1 = Player(1, 1)
    p2 = Player(3, 3)

    p1.move_to(2, 1)
    assert p1.get_position() == (2, 1)
    assert p2.get_position() == (3, 3)  # p2 ne doit pas avoir bougé

def test_player_invalid_types():
    with pytest.raises(TypeError):
        Player(True, 1)  # Les booléens sont interdits
    with pytest.raises(TypeError):
        Player(1, "y")    # Les str sont interdits