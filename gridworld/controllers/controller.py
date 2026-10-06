from gridworld.contracts import Action, InputSource


class Controller:
    """To implement. Read a key and translate it into an action."""

    def __init__(self, input_source: InputSource) -> None:
        raise NotImplementedError("store the input source")

    def key_to_action(self, key: str) -> Action | None:
        raise NotImplementedError("translate the key; return None if it is unknown")

    def get_action(self) -> Action | None:
        raise NotImplementedError("call input_source.read_key once and translate the result")
