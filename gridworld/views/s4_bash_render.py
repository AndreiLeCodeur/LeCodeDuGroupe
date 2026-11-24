"""SUPPLIED S4 terminal adapter; keep your existing BashRender unchanged."""
from gridworld.contracts import JsonState
from gridworld.views.bash_render import BashRender


S4_SYMBOLS = {
    "enemy.horizontal": "H", "enemy.vertical": "V", "enemy.chaser": "C",
    "actor.fake": "F", "star": "*", "player.invincible": "@",
}


def has_s4_content(state: JsonState) -> bool:
    return bool(state.get("extras", {}).get("invincible_turns", 0)) or any(
        entity.get("appearance") in S4_SYMBOLS for entity in state["entities"]
    )


class S4BashRender(BashRender):
    """Delegate old frames unchanged; display supplied S4 symbols when needed."""

    def state_to_string(self, json_state: JsonState) -> str:
        if not has_s4_content(json_state):
            return super().state_to_string(json_state)
        terrain = {"floor": ".", "wall": "#", "exit": "E"}
        rows = [[terrain.get(tile, "?") for tile in row]
                for row in json_state["level"]["tiles"]]
        symbols = {"player": "P", "sphinx": "S", **S4_SYMBOLS}
        for entity in json_state["entities"]:
            symbol = symbols.get(entity.get("appearance"), "?")
            rows[entity["y"]][entity["x"]] = symbol
        lines = ["".join(row) for row in rows]
        lines.append(f"Turn: {json_state['turn']}")
        if json_state["message"]:
            lines.append(json_state["message"])
        remaining = json_state.get("extras", {}).get("invincible_turns", 0)
        if remaining:
            lines.append(f"Invincible: {remaining} turns")
        return "\n".join(lines)

    def update_render(self, json_state: JsonState) -> None:
        if not has_s4_content(json_state):
            super().update_render(json_state)
        else:
            self.refresh(self.state_to_string(json_state))
