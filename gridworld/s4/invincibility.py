"""PR 2: independently testable effect, later owned by the player."""


class Invincibility:
    def __init__(self):
        self._remaining = 0

    @property
    def remaining(self) -> int:
        return self._remaining

    def activate(self, turns: int = 5) -> None:
        """Replace the duration (never add to it); reject negative values."""
        if turns < 0:
            raise ValueError("turns must not be negative")
        self._remaining = turns

    def tick(self) -> None:
        """Remove one phase, never going below zero."""
        if self._remaining > 0:
            self._remaining -= 1