import sys

from gridworld.contracts import JsonState


class BashRender:
    """To complete. Only refresh is supplied and must remain unchanged."""

    def __init__(self) -> None:
        raise NotImplementedError("initialize the terminal view")

    def start(self) -> None:
        raise NotImplementedError("start the view; a no-op is acceptable")

    def state_to_string(self, json_state: JsonState) -> str:
        #raise NotImplementedError("floor=., wall=#, exit=E; entities in order (player=P, unknown=?); turn and message, without print")

        #convertir le terrain
        tile_map = {
            "floor": ".",
            "wall": "#",
            "exit": "E",
        }


        #récupérer data
        grid_data = json_state.get("grid", {})
        width = grid_data.get("width", 0)
        height = grid_data.get("height", 0)
        tiles_input = grid_data.get("tiles", [])

        #construction de la grille
        grid = [
            [tile_map.get(tile, ".") for tile in row]
            for row in tiles_input
        ]

        #superposition des entités
        entities = json_state.get("entities", [])
        for entity in entities:
            x = entity.get("x")
            y = entity.get("y")
            entity_type = entity.get("type")

            char = "P" if entity_type == "player" else "?"

            if 0 <= y < height and 0 <= x < width:
                grid[y][x] = char

        board_lines = ["".join(row) for row in grid]
        board_str = "\n".join(board_lines)

        #ajout du tour et du message
        turn = json_state.get("turn", 0)
        message = json_state.get("message", "")

        return f"{board_str}\nTurn: {turn}\n{message}"        

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
        #raise NotImplementedError("call state_to_string then refresh, once each")
        rendered_text = self.state_to_string(json_state)
        self.refresh(rendered_text)

    def close(self) -> None:
        #raise NotImplementedError("close idempotently; a no-op is acceptable")
        self._closed = True