"""Supplied Pygame input: do not modify during S0."""
from collections import deque
import os
from typing import TYPE_CHECKING

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

if TYPE_CHECKING:
    from gridworld.views.pygame_render import PygameRender


class PygameInput:
    """Supplied input source: follows InputSource without translating keys into actions.

    The window connection stays inside the two supplied Pygame components.
    The controller only knows read_key; it never receives the renderer.
    """

    def __init__(self, renderer: "PygameRender") -> None:
        self._renderer = renderer
        self._window = None
        self._keys = deque()
        self._clock = pygame.time.Clock()

    def read_key(self) -> str | None:
        """Read at most one raw key without waiting for a keypress.

        Called regularly by Controller.get_action, even without movement.
        Keep the window responsive and limit polling to 60 reads per second.
        Never move an entity or modify the game state.
        """
        if self._renderer._screen is None:
            raise RuntimeError("Call renderer.start() before reading keyboard input.")
        if self._window is not self._renderer._screen:
            self._keys.clear()
            self._window = self._renderer._screen
        self._clock.tick(60)
        special = {pygame.K_UP: "ArrowUp", pygame.K_RIGHT: "ArrowRight",
                   pygame.K_DOWN: "ArrowDown", pygame.K_LEFT: "ArrowLeft",
                   pygame.K_ESCAPE: "Escape", pygame.K_SPACE: " "}
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._keys.append("Escape")
            elif event.type == pygame.KEYDOWN:
                key = special.get(event.key, getattr(event, "unicode", ""))
                if key:
                    self._keys.append(key)
            elif event.type == pygame.WINDOWEXPOSED:
                self._renderer._draw()
        return self._keys.popleft() if self._keys else None
