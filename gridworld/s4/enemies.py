"""PR 1: common implementation and three behaviors. No rendering code here."""
from gridworld.s4.contracts import Position, RandomSource, WorldView
from gridworld.contracts import EntityState


class BaseEnemy:
    kind = "enemy"

    def __init__(self, actor_id: str, x: int, y: int):
        raise NotImplementedError("PR 1: store identity and position")

    def get_position(self) -> Position:
        raise NotImplementedError("PR 1")

    def to_state(self) -> EntityState:
        raise NotImplementedError("PR 1: fresh public state with the subclass appearance")

    def update(self, world: WorldView, rng: RandomSource) -> None:
        raise NotImplementedError("Implement the concrete enemy behavior")


class HorizontalEnemy(BaseEnemy):
    appearance = "enemy.horizontal"

    def update(self, world: WorldView, rng: RandomSource) -> None:
        raise NotImplementedError("PR 1: horizontal patrol")


class VerticalEnemy(BaseEnemy):
    appearance = "enemy.vertical"

    def update(self, world: WorldView, rng: RandomSource) -> None:
        raise NotImplementedError("PR 1: vertical patrol")


class ChaserEnemy(BaseEnemy):
    appearance = "enemy.chaser"

    def update(self, world: WorldView, rng: RandomSource) -> None:
        raise NotImplementedError("PR 1: approach the player")
