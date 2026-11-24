"""PR 2: independent class; do not inherit BaseEnemy."""
from gridworld.contracts import EntityState
from gridworld.s4.contracts import Position, RandomSource, WorldView


class Star:
    kind = "star"

    def __init__(self, actor_id: str, x: int, y: int):
        self.id = actor_id
        self.x = x
        self.y = y
        self.visible = True
        self.collected = False

    def get_position(self) -> Position:
        return (self.x, self.y)

    def update(self, world: WorldView, rng: RandomSource) -> None:
        if self.collected:
            return
        if rng.random() < 0.5:  # strict: 0.5 does not toggle
            self.visible = not self.visible

    def to_state(self) -> EntityState | None:
        if not self.visible:
            return None
        return {
            "id": self.id,
            "kind": self.kind,
            "x": self.x,
            "y": self.y,
            "appearance": "star",
        }

    def collect(self) -> bool:
        if not self.visible or self.collected:
            return False
        self.collected = True
        self.visible = False
        return True