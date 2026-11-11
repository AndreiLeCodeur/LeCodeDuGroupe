import sys

from gridworld.contracts import JsonState


class BashRender:
    """To complete. Only refresh is supplied and must remain unchanged."""

    TILE_CHARS = {"floor": ".", "wall": "#", "exit": "E"}
    ENTITY_CHARS = {"player": "P"}

    def __init__(self) -> None:
        self._closed = False

    def start(self) -> None:
        # rien à initialiser pour le terminal
        self._closed = False

    def state_to_string(self, json_state: JsonState) -> str:
        """floor=., wall=#, exit=E; entities in order (player=P, unknown=?); turn and message.

        Ne modifie pas json_state et n'appelle pas print.
        """
        level = json_state["level"]
        # copie locale de la grille : on ne touche jamais au dictionnaire reçu
        grid = [[self.TILE_CHARS.get(tile, "?") for tile in row] for row in level["tiles"]]

        # superposition des entités dans l'ordre : la dernière gagne (le joueur est en dernier)
        for entity in json_state["entities"]:
            x, y = entity["x"], entity["y"]
            if 0 <= y < len(grid) and 0 <= x < len(grid[y]):
                grid[y][x] = self.ENTITY_CHARS.get(entity["appearance"], "?")

        board = "\n".join("".join(row) for row in grid)
        return f"{board}\nTurn: {json_state['turn']}\n{json_state['message']}"

    def refresh(self, text: str) -> None:
        """SUPPLIED: replace the ANSI terminal display without adding print calls.

        No resources or instance attributes are required. When output is
        redirected to a file, write plain text without control codes.
        """
        if not isinstance(text, str):
            raise TypeError("refresh expects a string")
        prefix = "\033[2J\033[H" if sys.stdout.isatty() else ""
        sys.stdout.write(prefix + text + ("" if text.endswith("\n") else "\n"))
        sys.stdout.flush()

    def update_render(self, json_state: JsonState) -> None:
        self.refresh(self.state_to_string(json_state))

    def close(self) -> None:
        # idempotent : on peut appeler close plusieurs fois sans erreur
        self._closed = True
