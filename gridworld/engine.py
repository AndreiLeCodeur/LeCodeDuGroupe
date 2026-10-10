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
