from gridworld.contracts import Action, InputSource


class Controller:
    """To implement. Read a key and translate it into an action."""

    def __init__(self, input_source: InputSource) -> None:
        self.input_source = input_source
        self.key_to_action_map: dict[str, Action] = {
        #les déplacements
        "z" : "north",
        "Z" : "north",
        "ArrowUp" : "north",

        "s" : "south",
        "S" : "south",
        "ArrowDown" : "south",

        "q" : "west",
        "Q" : "west",
        "ArrowLeft" : "west",

        "d" : "east",
        "D" : "east",
        "ArrowRight" : "east",

        #l'attente
        " " : "wait",

        #quitter
        ":quit" : "quit",
        "Escape" : "quit"

        }
        raise NotImplementedError("store the input source")

    def key_to_action(self, key: str) -> Action | None:
        if key is None: 
            return None
        return self.key_to_action_map.get(key)

    def get_action(self) -> Action | None:
        raw_key = self.input_source.read_key()
        return self.key_to_action(raw_key)
