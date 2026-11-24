"""PR 2: independently testable effect, later owned by the player."""


class Invincibility:
    def __init__(self):
        raise NotImplementedError("PR 2: start at zero")

    @property
    def remaining(self) -> int:
        raise NotImplementedError("PR 2")

    def activate(self, turns: int = 5) -> None:
        raise NotImplementedError("PR 2: replace duration; reject negative values")

    def tick(self) -> None:
        raise NotImplementedError("PR 2: decrement, never below zero")
