from gridworld.models.level import Level
from gridworld.models.player import Player
from gridworld.s4.turn_system import advance_phase, collect_at_player, resolve_contacts
from gridworld.s4.world import ActorWorld
from testing.s4_fakes import FakeActor, FakeInvincibility, FakeWorld, FixedRandom


class RecordingInvincibility(FakeInvincibility):
    def __init__(self, remaining=0):
        super().__init__(remaining)
        self.ticks = 0
        self.activations = []

    def activate(self, turns=5):
        self.activations.append(turns)
        super().activate(turns)

    def tick(self):
        self.ticks += 1
        super().tick()


class OrderedActor(FakeActor):
    """Records the order in which actors receive update()."""
    def __init__(self, log, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = log

    def update(self, world, rng):
        self.log.append(self.id)
        super().update(world, rng)


# --- Supplied starting tests ------------------------------------------------

def test_last_protected_phase_eliminates_an_enemy_that_moves_into_player():
    enemy = FakeActor("e-1", 2, 2, delta=(1, 0))
    actors = [enemy]
    world = FakeWorld(player=(3, 2))
    effect = FakeInvincibility(remaining=1)
    result = advance_phase(actors, world, effect, FixedRandom())
    assert result["status"] == "playing"
    assert result["actors"] is actors
    assert actors == []
    assert enemy.calls == 1
    assert effect.remaining == 0


def test_collect_only_once():
    star = FakeActor("star-1", 2, 2, kind="star")
    effect = FakeInvincibility()
    world = FakeWorld(player=(2, 2))
    collect_at_player([star], world, effect)
    assert effect.remaining == 5
    effect.tick()
    collect_at_player([star], world, effect)
    assert effect.remaining == 4


# --- collect_at_player ------------------------------------------------------

def test_hidden_star_grants_nothing():
    star = FakeActor("star-1", 2, 2, kind="star", visible=False)
    effect = RecordingInvincibility()
    collect_at_player([star], FakeWorld(player=(2, 2)), effect)
    assert effect.remaining == 0
    assert effect.activations == []
    assert not star.collected


def test_star_elsewhere_is_not_collected():
    star = FakeActor("star-1", 4, 4, kind="star")
    effect = RecordingInvincibility()
    collect_at_player([star], FakeWorld(player=(2, 2)), effect)
    assert effect.remaining == 0
    assert not star.collected


def test_enemy_on_player_cell_is_never_collected():
    enemy = FakeActor("e-1", 2, 2)
    effect = RecordingInvincibility()
    collect_at_player([enemy], FakeWorld(player=(2, 2)), effect)
    assert effect.activations == []
    assert not enemy.collected


def test_collection_does_not_tick():
    star = FakeActor("star-1", 2, 2, kind="star")
    effect = RecordingInvincibility()
    collect_at_player([star], FakeWorld(player=(2, 2)), effect)
    assert effect.activations == [5]
    assert effect.ticks == 0


# --- resolve_contacts -------------------------------------------------------

def test_unprotected_contact_is_a_defeat():
    enemy = FakeActor("e-1", 2, 2)
    actors = [enemy]
    result = resolve_contacts(actors, FakeWorld(player=(2, 2)), FakeInvincibility())
    assert result == {"actors": actors, "status": "lost"}
    assert result["actors"] is actors
    assert actors == [enemy]


def test_protected_contact_eliminates_only_touching_enemies_in_place():
    touching = FakeActor("e-1", 2, 2)
    distant = FakeActor("e-2", 5, 4)
    actors = [touching, distant]
    effect = RecordingInvincibility(remaining=3)
    result = resolve_contacts(actors, FakeWorld(player=(2, 2)), effect)
    assert result["status"] == "playing"
    assert result["actors"] is actors
    assert actors == [distant]
    assert effect.remaining == 3


def test_no_contact_keeps_playing():
    actors = [FakeActor("e-1", 4, 4)]
    result = resolve_contacts(actors, FakeWorld(player=(2, 2)), FakeInvincibility())
    assert result == {"actors": actors, "status": "playing"}


def test_star_on_player_is_never_an_enemy():
    star = FakeActor("star-1", 2, 2, kind="star")
    actors = [star]
    result = resolve_contacts(actors, FakeWorld(player=(2, 2)), FakeInvincibility(2))
    assert result["status"] == "playing"
    assert actors == [star]


def test_resolve_contacts_neither_updates_nor_ticks():
    enemy = FakeActor("e-1", 2, 2)
    effect = RecordingInvincibility(remaining=2)
    resolve_contacts([enemy], FakeWorld(player=(2, 2)), effect)
    assert enemy.calls == 0
    assert effect.ticks == 0


# --- advance_phase ----------------------------------------------------------

def test_initial_contact_is_resolved_before_the_enemy_escapes():
    enemy = FakeActor("e-1", 2, 2, delta=(1, 0))
    effect = RecordingInvincibility()
    result = advance_phase([enemy], FakeWorld(player=(2, 2)), effect, FixedRandom())
    assert result["status"] == "lost"
    assert enemy.calls == 0
    assert effect.ticks == 0


def test_enemy_entering_player_cell_is_a_defeat():
    enemy = FakeActor("e-1", 2, 2, delta=(1, 0))
    effect = RecordingInvincibility()
    result = advance_phase([enemy], FakeWorld(player=(3, 2)), effect, FixedRandom())
    assert result["status"] == "lost"
    assert enemy.get_position() == (3, 2)
    assert effect.ticks == 0


def test_defeat_stops_the_phase_immediately():
    log = []
    first = OrderedActor(log, "a", 2, 2, delta=(1, 0))
    later = OrderedActor(log, "b", 5, 4, delta=(0, 1))
    effect = RecordingInvincibility()
    result = advance_phase([later, first], FakeWorld(player=(3, 2)), effect,
                           FixedRandom())
    assert result["status"] == "lost"
    assert log == ["a"]
    assert later.calls == 0
    assert effect.ticks == 0


def test_each_actor_updates_once_in_id_order():
    log = []
    actors = [OrderedActor(log, "c", 1, 5), OrderedActor(log, "a", 1, 1),
              OrderedActor(log, "b", 1, 3)]
    advance_phase(actors, FakeWorld(player=(7, 5)), FakeInvincibility(), FixedRandom())
    assert log == ["a", "b", "c"]
    assert [actor.calls for actor in actors] == [1, 1, 1]


def test_invisible_star_still_updates():
    star = FakeActor("star-1", 4, 4, kind="star", visible=False)
    advance_phase([star], FakeWorld(player=(2, 2)), FakeInvincibility(), FixedRandom())
    assert star.calls == 1


def test_protection_of_one_covers_every_contact_of_the_phase():
    initial = FakeActor("a", 3, 2, delta=(0, 1))
    incoming = FakeActor("b", 2, 2, delta=(1, 0))
    actors = [initial, incoming]
    effect = RecordingInvincibility(remaining=1)
    result = advance_phase(actors, FakeWorld(player=(3, 2)), effect, FixedRandom())
    assert result["status"] == "playing"
    assert actors == []
    assert initial.calls == 0  # eliminated before it could act
    assert incoming.calls == 1
    assert effect.ticks == 1
    assert effect.remaining == 0


class PlayerShiftingWorld(FakeWorld):
    """Moves the player after the first query, so a later actor ends up touching."""
    def __init__(self, shifts, **kwargs):
        super().__init__(**kwargs)
        self.shifts = list(shifts)

    def can_enter(self, actor_id, x, y):
        allowed = super().can_enter(actor_id, x, y)
        if self.shifts:
            self.player = self.shifts.pop(0)
        return allowed


def test_eliminated_actor_is_skipped_later_in_the_phase():
    mover = FakeActor("a", 1, 1, delta=(0, 0))
    victim = FakeActor("b", 4, 4, delta=(1, 0))
    actors = [victim, mover]
    world = PlayerShiftingWorld(shifts=[(4, 4)], player=(2, 2))
    effect = RecordingInvincibility(remaining=2)
    result = advance_phase(actors, world, effect, FixedRandom())
    assert result["status"] == "playing"
    assert actors == [mover]
    assert victim.calls == 0
    assert effect.ticks == 1


def test_completed_phase_ticks_exactly_once():
    actors = [FakeActor("a", 1, 1), FakeActor("b", 1, 3), FakeActor("s", 5, 5, kind="star")]
    effect = RecordingInvincibility(remaining=3)
    result = advance_phase(actors, FakeWorld(player=(7, 5)), effect, FixedRandom())
    assert result["status"] == "playing"
    assert effect.ticks == 1
    assert effect.remaining == 2


def test_empty_phase_still_consumes_protection():
    effect = RecordingInvincibility(remaining=2)
    actors = []
    result = advance_phase(actors, FakeWorld(), effect, FixedRandom())
    assert result == {"actors": actors, "status": "playing"}
    assert effect.remaining == 1


def test_phase_does_not_move_the_player():
    world = FakeWorld(player=(5, 3))
    advance_phase([FakeActor("a", 1, 1)], world, FakeInvincibility(), FixedRandom())
    assert world.player == (5, 3)


# --- With a real map --------------------------------------------------------

ROOM = {
    "id": "turns",
    "grid": ["#######", "#.....#", "#.....#", "#######"],
    "start": {"x": 1, "y": 1},
    "exit": {"x": 5, "y": 2},
}


def test_elimination_frees_the_cell_for_following_actors_in_actor_world():
    level, player = Level(ROOM), Player(3, 1)
    actors = []
    world = ActorWorld(level, player, actors)
    blocker = FakeActor("a", 3, 1)  # on the player, eliminated first
    follower = FakeActor("b", 2, 1, delta=(1, 0))
    actors.extend([blocker, follower])
    effect = FakeInvincibility(remaining=1)
    result = advance_phase(actors, world, effect, FixedRandom())
    assert result["status"] == "playing"
    assert result["actors"] is actors
    assert actors == []
    assert follower.calls == 1
    assert effect.remaining == 0
