"""PR 4: test independently of Engine with the supplied doubles."""
from typing import Literal, TypedDict
from gridworld.s4.contracts import InvincibilityEffect, RandomSource, TurnActor, WorldView


class PhaseResult(TypedDict):
    actors: list[TurnActor]
    status: Literal["playing", "lost"]


def collect_at_player(actors: list[TurnActor], world: WorldView,
                      effect: InvincibilityEffect) -> None:
    raise NotImplementedError("PR 4: collect a visible star on player entry; activate five phases")


def resolve_contacts(actors: list[TurnActor], world: WorldView,
                     effect: InvincibilityEffect) -> PhaseResult:
    raise NotImplementedError("PR 4: only enemies cause defeat or are eliminated")


def advance_phase(actors: list[TurnActor], world: WorldView,
                  effect: InvincibilityEffect, rng: RandomSource) -> PhaseResult:
    raise NotImplementedError("PR 4: contacts before/after each actor, stop on defeat, tick once")
