from gridworld.contracts import LevelState
from gridworld.models.tile import Tile


class LevelError(ValueError):
    """JSON loading error or violation of the map contract."""


class Level:
    """To implement. Terrain grid loaded from levels/n0.json."""

    def __init__(self, data: dict) -> None:
        raise NotImplementedError("validate the map and create its tiles")

    @classmethod
    def load(cls, path: str) -> "Level":
        raise NotImplementedError("read JSON and convert errors to LevelError")

    def get_start(self) -> tuple[int, int]:
        raise NotImplementedError("return the starting coordinates")

    def get_tile(self, x: int, y: int) -> Tile:
        raise NotImplementedError("look up a tile; raise IndexError outside the grid")

    def is_walkable(self, x: int, y: int) -> bool:
        raise NotImplementedError("query the tile; return False outside the grid")

    def is_exit(self, x: int, y: int) -> bool:
        raise NotImplementedError("query the tile; return False outside the grid")

    def to_state(self) -> LevelState:
        raise NotImplementedError("create a new independent level state")
