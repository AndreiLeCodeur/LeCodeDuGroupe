class TerminalInput:
    """To implement. Input source following the InputSource Protocol."""

    def read_key(self) -> str | None:
        """Use input() followed by Enter; return :quit on EOF or interruption."""
        try:
            return input()
        except (EOFError, KeyboardInterrupt):
            return ":quit"
