from gridworld.contracts import Action, JsonState, Renderer
from gridworld.controllers.controller import Controller
from gridworld.models.level import Level
from gridworld.models.player import Player


class Engine:
    """Game transitions without I/O, and game orchestration."""
    def __init__(self, level: Level, controller: Controller, renderer: Renderer) -> None:
        self.level = level
        self.controller = controller
        self.renderer = renderer

        x, y = level.get_start()
        self.player = Player(x, y)

        self.status = "playing"
        self.turn = 0
        self.message = ""
        self.interaction = None
        self.extras = {}

    def get_action(self) -> Action | None:
        return self.controller.get_action()

    def apply_action(self, action: Action) -> None:
        ...
        move_map = {
            "north": (0, -1),
            "east": (1, 0),
            "south": (0, 1),
            "west": (-1, 0),
            "wait": (0, 0),
            "quit": (0, 0),
        }

        if action not in move_map:
            raise ValueError(f"Action inconnue: {action!r}")

        if action == "quit":
            self.status = "lost"
            self.message = "You quit the game."
            return

        if action == "wait":
            self.turn += 1
            self.message = "You wait."
            return

        x, y = self.player.get_position()
        dx, dy = move_map[action]
        next_x = x + dx
        next_y = y + dy

        if not self.level.is_walkable(next_x, next_y):
            self.message = "Blocked."
            return

        self.player.move_to(next_x, next_y)
        self.turn += 1

        if self.level.is_exit(next_x, next_y):
            self.status = "won"
            self.message = "Victory!"
        else:
            self.message = "You moved."


    def get_state(self) -> JsonState:
        return {
            "level": self.level.to_state(),
            "entities": [self.player.to_state()],
            "player_id": "player-1",
            "status": self.status,
            "turn": self.turn,
            "message": self.message,
            "interaction": self.interaction,
            "extras": self.extras,
        }

    def render(self, json_state: JsonState) -> None:
        self.renderer.update_render(json_state)

    def run(self) -> None:
        self.render(self.get_state())
        while self.status == "playing":
            action = self.get_action()
            if action is None:
                continue
            if action == "quit":
                break
            self.apply_action(action)
            self.render(self.get_state())
