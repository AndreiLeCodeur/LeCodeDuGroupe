"""PR 2: independent class; do not inherit BaseEnemy."""
from gridworld.s4.contracts import Position, RandomSource, WorldView
from gridworld.contracts import EntityState


class Star:
    kind = "star"

    def __init__(self, actor_id: str, x: int, y: int):
        raise NotImplementedError("PR 2: identity, position, visible and collected flags")

    def get_position(self) -> Position:
        raise NotImplementedError("PR 2")

    def update(self, world: WorldView, rng: RandomSource) -> None:
        raise NotImplementedError("PR 2: toggle with probability 1/2, unless collected")

    def to_state(self) -> EntityState | None:
        raise NotImplementedError("PR 2: visible public state or None")

    def collect(self) -> bool:
        raise NotImplementedError("PR 2: collect once, only when visible")
