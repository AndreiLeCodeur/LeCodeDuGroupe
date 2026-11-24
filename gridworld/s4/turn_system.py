"""PR 4: test independently of Engine with the supplied doubles."""
from typing import Literal, TypedDict, cast

from gridworld.s4.contracts import (
    Collectible,
    InvincibilityEffect,
    RandomSource,
    TurnActor,
    WorldView,
)

STAR_DURATION = 5


class PhaseResult(TypedDict):
    actors: list[TurnActor]
    status: Literal["playing", "lost"]


def collect_at_player(actors: list[TurnActor], world: WorldView,
                      effect: InvincibilityEffect) -> None:
    """Collect visible stars on the player's cell; never ticks the effect."""
    player = world.get_player_position()
    for actor in actors:
        if actor.kind != "star" or actor.get_position() != player:
            continue
        if cast(Collectible, actor).collect():
            effect.activate(STAR_DURATION)


def resolve_contacts(actors: list[TurnActor], world: WorldView,
                     effect: InvincibilityEffect) -> PhaseResult:
    """Defeat on enemy contact, or eliminate touching enemies when protected.

    The list is shared with the world: removals happen in place.
    """
    player = world.get_player_position()
    touching = [actor for actor in actors
                if actor.kind == "enemy" and actor.get_position() == player]
    if not touching:
        return {"actors": actors, "status": "playing"}
    if effect.remaining <= 0:
        return {"actors": actors, "status": "lost"}
    eliminated = {id(actor) for actor in touching}
    actors[:] = [actor for actor in actors if id(actor) not in eliminated]
    return {"actors": actors, "status": "playing"}


def advance_phase(actors: list[TurnActor], world: WorldView,
                  effect: InvincibilityEffect, rng: RandomSource) -> PhaseResult:
    """Run one enemy phase: contacts before/after each actor, tick once at the end."""
    result = resolve_contacts(actors, world, effect)
    if result["status"] == "lost":
        return result
    for actor in sorted(actors, key=lambda actor: actor.id):
        if not any(alive is actor for alive in actors):
            continue
        actor.update(world, rng)
        result = resolve_contacts(actors, world, effect)
        if result["status"] == "lost":
            return result
    effect.tick()
    return {"actors": actors, "status": "playing"}
