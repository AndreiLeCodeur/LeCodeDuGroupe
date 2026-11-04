import pytest
from gridworld.models.tile import Tile

def test_tile_walkable_and_exit():
    floor = Tile("floor")
    assert floor.is_walkable() is True
    assert floor.is_exit() is False

    exit_tile = Tile("exit")
    assert exit_tile.is_walkable() is True
    assert exit_tile.is_exit() is True

    wall = Tile("wall")
    assert wall.is_walkable() is False
    assert wall.is_exit() is False

def test_unknown_tile_raises_value_error():
    with pytest.raises(ValueError):
        Tile("unknown_type")