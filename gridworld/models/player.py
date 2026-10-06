from gridworld.contracts import EntityState


class Player:
    """To implement. Player position; collisions belong to the engine."""

    def __init__(self, x: int, y: int) -> None:
        raise NotImplementedError("store integer coordinates, excluding bool")

    def get_position(self) -> tuple[int, int]:
        raise NotImplementedError("return x, y")

    def move_to(self, x: int, y: int) -> None:
        raise NotImplementedError("update coordinates validated by the engine")

    def to_state(self) -> EntityState:
        raise NotImplementedError("return id=player-1, kind=player, x, y, appearance=player in a new dict")
