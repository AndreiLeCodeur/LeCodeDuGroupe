import sys

from gridworld.contracts import JsonState


class BashRender:
    """To complete. Only refresh is supplied and must remain unchanged."""

    def __init__(self) -> None:
        raise NotImplementedError("initialize the terminal view")

    def start(self) -> None:
        raise NotImplementedError("start the view; a no-op is acceptable")

    def state_to_string(self, json_state: JsonState) -> str:
        raise NotImplementedError("floor=., wall=#, exit=E; entities in order (player=P, unknown=?); turn and message, without print")

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
        raise NotImplementedError("call state_to_string then refresh, once each")

    def close(self) -> None:
        raise NotImplementedError("close idempotently; a no-op is acceptable")
