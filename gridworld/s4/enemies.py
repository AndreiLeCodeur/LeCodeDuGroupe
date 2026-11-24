"""PR 1: common implementation and three behaviors. No rendering code here.

``BaseEnemy`` shares identity, position and public state between the three
enemies. Each subclass only defines its appearance and overrides ``update``.
The behaviors are adapted from ``legacy_enemies.py``.
"""
from gridworld.contracts import EntityState
from gridworld.s4.contracts import Position, RandomSource, WorldView

# Order tried by the chaser: north, east, south, west.
CHASER_STEPS: tuple[Position, ...] = ((0, -1), (1, 0), (0, 1), (-1, 0))


class BaseEnemy:
    kind = "enemy"
    appearance: str

    def __init__(self, actor_id: str, x: int, y: int):
        self.id = actor_id
        self.x = x
        self.y = y

    def get_position(self) -> Position:
        return self.x, self.y

    def to_state(self) -> EntityState:
        return {"id": self.id, "kind": self.kind, "x": self.x, "y": self.y,
                "appearance": self.appearance}

    def update(self, world: WorldView, rng: RandomSource) -> None:
        raise NotImplementedError("Implement the concrete enemy behavior")

    def _try_move(self, world: WorldView, nx: int, ny: int) -> bool:
        """Move to (nx, ny) only if the world allows it; report success."""
        if not world.can_enter(self.id, nx, ny):
            return False
        self.x, self.y = nx, ny
        return True


class HorizontalEnemy(BaseEnemy):
    appearance = "enemy.horizontal"

    def __init__(self, actor_id: str, x: int, y: int):
        super().__init__(actor_id, x, y)
        self.direction = 1  # starts east

    def update(self, world: WorldView, rng: RandomSource) -> None:
        if not self._try_move(world, self.x + self.direction, self.y):
            self.direction = -self.direction  # turn back, stay this turn


class VerticalEnemy(BaseEnemy):
    appearance = "enemy.vertical"

    def __init__(self, actor_id: str, x: int, y: int):
        super().__init__(actor_id, x, y)
        self.direction = 1  # starts south

    def update(self, world: WorldView, rng: RandomSource) -> None:
        if not self._try_move(world, self.x, self.y + self.direction):
            self.direction = -self.direction  # turn back, stay this turn


class ChaserEnemy(BaseEnemy):
    appearance = "enemy.chaser"

    def update(self, world: WorldView, rng: RandomSource) -> None:
        px, py = world.get_player_position()
        distance = abs(self.x - px) + abs(self.y - py)
        for dx, dy in CHASER_STEPS:
            nx, ny = self.x + dx, self.y + dy
            if abs(nx - px) + abs(ny - py) < distance and self._try_move(world, nx, ny):
                return
        # No permitted step reduces the distance: wait.
