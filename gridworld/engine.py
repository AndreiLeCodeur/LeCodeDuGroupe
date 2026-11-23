import copy

from gridworld.contracts import Action, JsonState, Renderer
from gridworld.controllers.controller import Controller
from gridworld.models.level import Level
from gridworld.models.player import Player
from gridworld.web_support import new_interaction


class Engine:
    """Game transitions without I/O, and game orchestration."""
    def __init__(self, level: Level, controller: Controller, renderer: Renderer) -> None:
        self.level = level
        self.controller = controller
        self.renderer = renderer

        x, y = level.get_start()
        self.player = Player(x, y)

        # False once the player quits; the web server refuses actions afterwards
        self.running = True
        self.status = "playing"
        self.turn = 0
        self.message = ""
        self.sphinx = None
        self.interaction = None
        self.extras = {}

    def get_action(self) -> Action | None:
        return self.controller.get_action()

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

        # Quitter ferme la session, même après une victoire
        if action == "quit":
            self.running = False
            self.interaction = None

        # Partie terminée (victoire ou abandon) : plus aucune action ne modifie l'état
        if self.status != "playing":
            return

        if action == "quit":
            self.status = "lost"
            self.message = "You quit the game."
            return

        # Pendant un dialogue avec le sphinx, les déplacements et l'attente sont ignorés sans consommer de tour
        if self.interaction is not None:
            return

        if action == "wait":
            self.turn += 1
            self.message = "You wait."
            return

        x, y = self.player.get_position()
        dx, dy = move_map[action]
        next_x = x + dx
        next_y = y + dy

        # Chaque tentative de déplacement, y compris bloquée ou déclenchant le sphinx, consomme un tour
        self.turn += 1

        if not self.level.is_walkable(next_x, next_y):
            self.message = "Blocked."
            return

        # Rencontre avec le sphinx qui garde la sortie
        if self.level.is_exit(next_x, next_y) and self.sphinx is not None:
            self.start_sphinx_dialogue()
            return

        self.player.move_to(next_x, next_y)

        if self.level.is_exit(next_x, next_y):
            self.status = "won"
            self.message = "Victory!"
        else:
            self.message = "You moved."

    def start_sphinx_dialogue(self) -> None:
        """Keep the player in place and publish the cached question."""
        self.interaction = new_interaction(self.sphinx)

    def apply_sphinx_verdict(self, verdict: dict) -> None:
        """Apply a validated result without consuming another turn."""
        if not verdict["correct"]:
            if self.interaction is not None:
                self.interaction["status"] = "rejected"
                self.interaction["message"] = verdict["message"]
        else:
            sphinx_entity = self.level.get_sphinx()
            self.player.move_to(sphinx_entity["x"], sphinx_entity["y"])
            self.interaction = None
            self.status = "won"
            self.message = "Victory!"

    def get_state(self) -> JsonState:
        # deepcopy : l'appelant ne doit pas pouvoir modifier l'état interne (extras imbriqués...)
        entities = [self.player.to_state()]
        # le sphinx est une entité publique seulement si la carte en déclare un
        sphinx = self.level.get_sphinx()
        if sphinx is not None:
            entities.append(sphinx)

        return copy.deepcopy({
            "level": self.level.to_state(),
            "entities": entities,
            "player_id": "player-1",
            "status": self.status,
            "turn": self.turn,
            "message": self.message,
            "interaction": self.interaction,
            "extras": self.extras,
        })

    def render(self, json_state: JsonState) -> None:
        self.renderer.update_render(json_state)

    def run(self) -> None:
        # Rendu initial puis boucle jusqu'à "quit" ; après la victoire les actions sont ignorées
        self.render(self.get_state())
        while True:
            action = self.get_action()
            if action is None:
                continue
            if action == "quit":
                self.running = False
                break
            self.apply_action(action)
            self.render(self.get_state())


def next_turn(turn):
    return trun + 1
