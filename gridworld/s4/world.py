"""SUPPLIED read-only adapter; keeps a live reference to the actor collection."""
from gridworld.models.level import Level
from gridworld.models.player import Player
from gridworld.s4.contracts import Position, TurnActor


class ActorWorld:
    def __init__(self, level: Level, player: Player, actors: list[TurnActor]):
        self._level, self._player, self._actors = level, player, actors

    def get_player_position(self) -> Position:
        return self._player.get_position()

    def can_enter(self, actor_id: str, x: int, y: int) -> bool:
        if not self._level.is_walkable(x, y) or self._level.is_exit(x, y):
            return False
        return not any(actor.kind == "enemy" and actor.id != actor_id
                       and actor.get_position() == (x, y) for actor in self._actors)
