"""PR 3: constructors can be injected while the other PRs are unfinished."""
from collections.abc import Callable, Mapping
from gridworld.s4.contracts import TurnActor, WorldView

ActorConstructor = Callable[[str, int, int], TurnActor]


def create_actor(data: dict, constructors: Mapping[str, ActorConstructor]) -> TurnActor:
    raise NotImplementedError("PR 3: validate type/id/x/y and call the selected constructor")


def load_actors(data: list[dict], world: WorldView,
                constructors: Mapping[str, ActorConstructor]) -> list[TurnActor]:
    raise NotImplementedError("PR 3: validate unique ids and legal initial positions")
