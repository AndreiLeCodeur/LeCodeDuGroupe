"""SUPPLIED: agree on these contracts before parallel contributions."""
from typing import Literal, Protocol, TypedDict

from gridworld.contracts import EntityState

Position = tuple[int, int]
ActorKind = Literal["enemy", "star"]


class RandomSource(Protocol):
    def random(self) -> float:
        """Return a number in [0, 1). random.Random satisfies this contract."""
        ...


class WorldView(Protocol):
    def get_player_position(self) -> Position: ...

    def can_enter(self, actor_id: str, x: int, y: int) -> bool:
        """Check terrain and other enemies, without moving anything.

        The player and stars do not block an enemy: contact is resolved by the
        turn system immediately after movement. No method here mutates the world.
        """
        ...


class TurnActor(Protocol):
    id: str
    kind: ActorKind

    def get_position(self) -> Position: ...

    def update(self, world: WorldView, rng: RandomSource) -> None:
        """Advance this actor once; never mutate the player or other actors.

        An enemy may move at most one cardinal cell, after can_enter returns
        True. An invisible star still receives this call. Do not advance the
        global turn or render anything here.
        """
        ...

    def to_state(self) -> EntityState | None:
        """Return fresh public data, or None when invisible; never remove self."""
        ...


class Collectible(TurnActor, Protocol):
    def collect(self) -> bool:
        """Return True exactly once when visible; hide permanently on success."""
        ...


class InvincibilityEffect(Protocol):
    @property
    def remaining(self) -> int: ...

    def activate(self, turns: int = 5) -> None:
        """Replace the duration. Reject a negative duration."""
        ...

    def tick(self) -> None:
        """Consume one enemy phase, never below zero."""
        ...


class ActorSpec(TypedDict):
    type: Literal["horizontal", "vertical", "chaser", "star"]
    id: str
    x: int
    y: int
