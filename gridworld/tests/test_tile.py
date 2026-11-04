import pytest
from gridworld.models.tile import Tile

# On teste ici si les dalles sont bien praticables
def test_floor_is_walkable():
    tile = Tile("floor")
    assert tile.is_walkable() is True

def test_exit_is_exit():
    tile = Tile("exit")
    assert tile.is_exit() is True

def test_floor_to_state_returns_floor():
    tile = Tile("floor")
    assert tile.to_state() == "floor"
def test_wall_to_state_returns_wall():
    tile = Tile("wall")
    assert tile.to_state() == "wall"
def test_exit_to_state_returns_exit():
    tile = Tile("exit")
    assert tile.to_state() == "exit"