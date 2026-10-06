from gridworld.contracts import Action, JsonState, Renderer
from gridworld.controllers.controller import Controller
from gridworld.models.level import Level


class Engine:
    """To implement. Game transitions without I/O, and game orchestration."""

    def __init__(self, level: Level, controller: Controller, renderer: Renderer) -> None:
        raise NotImplementedError("initialize the game without rendering or starting the view")

    def get_action(self) -> Action | None:
        raise NotImplementedError("delegate to the controller")

    def apply_action(self, action: Action) -> None:
        raise NotImplementedError("apply a transition without input/output")

    def get_state(self) -> JsonState:
        raise NotImplementedError("build the shared JsonState: terrain, entities (player last), player_id, interaction=None in S0")

    def render(self, json_state: JsonState) -> None:
        raise NotImplementedError("forward this state to the renderer")

    def run(self) -> None:
        raise NotImplementedError("render, then loop until quit without busy-waiting")
