import json


from gridworld.contracts import Action, JsonState, Renderer
from gridworld.controllers.controller import Controller
from gridworld.models.level import Level

from gridworld.models.player import Player

class Engine:
    """To implement. Game transitions without I/O, and game orchestration."""

    def __init__(self, level: Level, controller: Controller, renderer: Renderer) -> None:

        with open("initial_state.json") as file :
            init_state = json.load(file)

        self.level = level
        self.controller = controller
        self.renderer = renderer

        #implement boucle pour trouver l'indice du joueur

        x,y = init_state["entities"][0]['x'], init_state["entities"][0]['y']

        self.player = Player(x,y)

        self.turn = init_state["turn"]
        self.message = init_state["message"]

        self.interaction = init_state["interaction"]
        self.extras = init_state["extras"]

    def get_action(self) -> Action | None:
        self.action_todo = self.controller.get_action()

    def apply_action(self, action: Action) -> None:
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
        raise NotImplementedError("build the shared JsonState: terrain, entities (player last), player_id, interaction=None in S0")

    def render(self, json_state: JsonState) -> None:
        raise NotImplementedError("forward this state to the renderer")

    def run(self) -> None:
        raise NotImplementedError("render, then loop until quit without busy-waiting")
    
