"""SUPPLIED wrapper for observing the inconsistent old enemy interfaces."""
from gridworld.s4.legacy_enemies import HorizontalGuard, Hunter, VerticalGuard


def legacy_trace(kind, actor_id, x, y, world, turns):
    constructors = {"horizontal": HorizontalGuard, "vertical": VerticalGuard,
                    "chaser": Hunter}
    actor = constructors[kind](actor_id, x, y)
    states = []
    for _ in range(turns):
        if kind == "horizontal":
            actor.walk(world)
            states.append(actor.as_entity())
        elif kind == "vertical":
            actor.advance(world)
            states.append(actor.dump())
        else:
            actor.chase(world.get_player_position(), world)
            states.append(actor.snapshot())
    return states
