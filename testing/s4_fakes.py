"""SUPPLIED deterministic doubles. Keep these in tests, not the real game."""
from gridworld.s4.contracts import ActorKind, Position


class FixedRandom:
    def __init__(self, value: float = 0.25):
        if not 0 <= value < 1:
            raise ValueError("value must be in [0, 1)")
        self.value = value

    def random(self) -> float:
        return self.value


class FakeWorld:
    def __init__(self, width=9, height=7, blocked=(), player=(1, 1)):
        self.width, self.height = width, height
        self.blocked = set(blocked)
        self.player = player
        self.queries = []

    def get_player_position(self) -> Position:
        return self.player

    def can_enter(self, actor_id, x, y) -> bool:
        self.queries.append((actor_id, x, y))
        return (0 < x < self.width - 1 and 0 < y < self.height - 1
                and (x, y) not in self.blocked)


class FakeActor:
    """No BaseEnemy inheritance; still satisfies TurnActor structurally."""
    def __init__(self, actor_id="fake-1", x=2, y=2, delta=(1, 0),
                 kind: ActorKind = "enemy", visible=True):
        self.id, self.kind = actor_id, kind
        self.x, self.y = x, y
        self.delta, self.visible = delta, visible
        self.calls = 0
        self.collected = False

    def get_position(self) -> Position:
        return self.x, self.y

    def update(self, world, rng) -> None:
        self.calls += 1
        dx, dy = self.delta
        if self.kind == "enemy" and world.can_enter(self.id, self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy

    def to_state(self):
        if not self.visible or self.collected:
            return None
        return {"id": self.id, "kind": self.kind, "x": self.x, "y": self.y,
                "appearance": "star" if self.kind == "star" else "actor.fake"}

    def collect(self) -> bool:
        if not self.visible or self.collected:
            return False
        self.collected, self.visible = True, False
        return True


class FakeInvincibility:
    def __init__(self, remaining=0):
        self.remaining = remaining

    def activate(self, turns=5):
        if turns < 0:
            raise ValueError("turns must be nonnegative")
        self.remaining = turns

    def tick(self):
        self.remaining = max(0, self.remaining - 1)


def recording_constructor(calls):
    """Factory double: inspect arguments without importing unfinished classes."""
    def construct(actor_id, x, y):
        calls.append((actor_id, x, y))
        return FakeActor(actor_id, x, y)
    return construct
