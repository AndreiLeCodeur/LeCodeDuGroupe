# Shared S4 contract

## Two separate relationships

BaseEnemy shares implementation between horizontal, vertical and chasing enemies.
Star does not inherit BaseEnemy. Both kinds satisfy TurnActor through their
attributes and methods; inheriting the Protocol is not required. An annotation
is not a runtime validator. Test behavior explicitly.

Each object has a stable id, kind (enemy or star), get_position(), update(world,
rng) and to_state(). State dictionaries must be fresh, JSON-serializable data
with id/kind/x/y/appearance. None means invisible, not deleted from simulation.

WorldView is supplied to update. can_enter checks walls, bounds and other live
enemies (excluding actor_id); it allows contact with the player and does not
block on stars. The real world view must see moves already made this phase.
Only the actor's own position/visibility may change inside its update. It never
increments Engine.turn, calls another actor, renders, or changes the player.

RandomSource.random() is enough for this session; use an injected random.Random
in the game and FixedRandom in tests. No module-level random calls or clocks.
Collectible adds collect() to the actor contract. The only star class implements
it; successful collection hides it permanently. Keep its identity in the world
or remove it after collection, but never let it reappear. A merely invisible,
uncollected star keeps updating. Each star has probability 1/2 of toggling.

## Common construction

Concrete constructors take (actor_id: str, x: int, y: int). A map extends the S2
JSON with optional actors (absent means []). Entries have type/id/x/y. Allowed
types: horizontal, vertical, chaser, star. Reject unknown types, duplicate or
reserved ids (player-1/sphinx-1), non-integer coordinates (including booleans),
out-of-bounds/wall positions and overlapping initial actors. Reserve the start
and exit so existing victory and sphinx behavior stay simple.
The final integration assembles the constructor dictionary. PR 3 can supply
recording constructors with the same signature and work independently.

## Behaviors preserved by the refactoring

Horizontal starts east; vertical starts south. A blocked patrol reverses its
stored direction but stays in place for this turn; it tries the opposite way on
the next turn. The chaser tries north/east/south/west in that order, taking the
first permitted step that strictly reduces Manhattan distance to the player.
It waits if none works. These algorithms are supplied in legacy_enemies.py.
No pathfinding, random movement, combat points or animation work is requested.
A star starts visible and uncollected. It toggles when random() < 0.5.

## Collection ownership and parallel work

ActorWorld is supplied in world.py. It sees the SAME mutable actors list as the
turn system. Resolve eliminations with an in-place update (actors[:] = survivors),
not rebinding to another list. PhaseResult["actors"] refers to that same list.
Iterate over a sorted snapshot and skip actors that have been removed. The
read-only WorldView always sees the most recent positions and eliminations.
The phase functions never change Engine.turn or the player's position.
collect_at_player activates the effect; it does not decrement it or run a phase.
Use kind == "star" and the supplied Collectible contract for collect(), not an
isinstance check against the unfinished concrete Star class. With type hints,
typing.cast(Collectible, actor) documents this contract; it is not runtime checking.
Invincibility starts at zero. An invalid negative duration raises ValueError.

Factory input: dictionaries with exactly type/id/x/y. Id is a nonblank string,
coordinates are int (not bool); unknown types and missing constructors raise
ValueError. load_actors accepts only a list, checks overlap/start/reserved cells
and calls create_actor. It returns a new list; it never moves the player or
mutates the supplied world. No global singleton objects or eval.

## Order fixed before integration

1. Ignore actions after won/lost or during sphinx dialogue (quit still works).
2. Apply the player's move/wait using existing rules. A blocked move consumes
   a turn; no input and quit do not. If the player enters a visible star's cell,
   collect it and activate five phases. Waiting on a newly visible star does not
   count as entering it: leave and return to collect it.
3. Preserve existing exit behavior. Winning or opening the sphinx dialogue ends
   this turn before actors act. Actor starting positions exclude the exit;
   WorldView.can_enter must also reserve the exit from enemies.
4. Resolve player/enemy contact before any enemy can escape. Without the effect,
   return lost; with it, remove colliding enemies before they can update.
5. Visit surviving actors by sorted id, update once, resolve contacts immediately
   after each. Stars do not cause defeat. Stop on defeat; do not update a removed
   enemy. A star appearing underneath the player does not trigger collection.
6. Decrement invincibility once after a completed actor phase, not on GET,
   dialogue answers, quit or after a win. Collection protects this phase plus the
   next four; a second star replaces the duration with five, it does not add five.
7. Increment the game turn exactly once for the player's accepted action and
   publish state, with positive remaining duration in extras.invincible_turns.
   Omit that optional key at zero (the supplied HUD defaults to zero); preserve
   other extras keys. This keeps old S0/S2 snapshots exactly compatible. Keep all
   existing S2 fields, player last and independent snapshots.

FakeWorld is a small test double, not an implementation of all real occupancy
rules. ActorWorld implements those rules; test it with real actors at integration.
