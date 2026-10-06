"""Supplied renderer: do not modify during S0.

Interface: start(), update_render(state), close().
Keyboard input: Controller(input_source=PygameInput(renderer)).
All methods are called on the main thread.

Embedded sprites: Kenney Tiny Dungeon (tile_0048, tile_0040, tile_0084,
tile_0036), CC0, https://kenney.nl/assets/tiny-dungeon
License: https://creativecommons.org/publicdomain/zero/1.0/
Images are embedded in this file; PygameInput is supplied in controllers/.
"""
from base64 import b64decode
from copy import deepcopy
from io import BytesIO
import json
import os
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame
from gridworld.contracts import JsonState


class PygameRender:
    """Supplied view, compatible with Renderer without requiring inheritance."""

    def __init__(self) -> None:
        self._screen = None
        self._state = None
        self._sprites = {}

    def start(self) -> None:
        if self._screen is not None:
            return
        pygame.display.init()
        pygame.font.init()
        try:
            self._screen = pygame.display.set_mode((560, 390))
            pygame.display.set_caption("Gridworld · Level 0")
            self._font = pygame.font.Font(None, 26)
            self._small = pygame.font.Font(None, 21)
            self._sprites = {
                name: pygame.transform.scale(
                    pygame.image.load(BytesIO(b64decode(data)), name + ".png").convert_alpha(),
                    (48, 48),
                ) for name, data in _IMAGES.items()
            }
            self._draw()
        except Exception:
            self.close()
            raise

    def update_render(self, json_state: JsonState) -> None:
        # A rendering snapshot, never a reference to the student model.
        snapshot = deepcopy(json_state)
        json.dumps(snapshot, allow_nan=False)
        self._state = snapshot
        if self._screen is not None:
            self._draw()

    def close(self) -> None:
        if self._screen is not None:
            pygame.display.quit()
            pygame.font.quit()
            self._screen = None
        self._sprites.clear()

    def _text(self, text, position, color=(219, 227, 215), small=False):
        font = self._small if small else self._font
        self._screen.blit(font.render(text, True, color), position)

    def _sprite(self, appearance, position):
        image = self._sprites.get(appearance)
        if image is not None:
            self._screen.blit(image, position)
        else:
            rect = pygame.Rect(position, (48, 48))
            pygame.draw.rect(self._screen, (121, 69, 99), rect.inflate(-6, -6), border_radius=5)
            self._text("?", (position[0] + 18, position[1] + 14))

    def _draw(self):
        state = self._state
        if state is None:
            self._screen.fill((24, 35, 40))
            self._text("Waiting for the first state…", (24, 36))
            pygame.display.flip()
            return
        level = state["level"]
        width, height = level["width"], level["height"]
        size = (max(560, width * 48 + 48), height * 48 + 150)
        if self._screen.get_size() != size:
            self._screen = pygame.display.set_mode(size)
        self._screen.fill((24, 35, 40))
        self._text(f"Level {level['id']}", (24, 20))
        self._text(f"Turn: {state['turn']}", (size[0] - 120, 20))
        left, top = (size[0] - width * 48) // 2, 62
        for y, row in enumerate(level["tiles"]):
            for x, appearance in enumerate(row):
                position = (left + x * 48, top + y * 48)
                self._sprite("floor", position)
                if appearance != "floor":
                    self._sprite(appearance, position)
        for entity in state["entities"]:
            self._sprite(entity["appearance"], (left + entity["x"] * 48, top + entity["y"] * 48))
        self._text(state["message"], (24, top + height * 48 + 12), (246, 207, 112))
        self._text("Arrows / ZQSD · Space: wait · Escape: quit", (24, size[1] - 28), small=True)
        pygame.display.flip()


# Original 16 × 16 PNG sprites, scaled without interpolation.
_IMAGES = {'floor': 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAAXNSR0IArs4c6QAAAB1JREFUOI1jfLU05z8DBYCJEs2jBowaMGrAYDIAAFXwAxr14JwoAAAAAElFTkSuQmCC', 'wall': 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQAgMAAABinRfyAAAABGdBTUEAALGPC/xhBQAAAAlQTFRFwMvcUmB8i5u0Ok/JaAAAACJJREFUCNdjCAUChlXLGGYBiVVQAizGCRRkWAnkQwgi1QEA9oIgs6OaBGAAAAAASUVORK5CYII=', 'player': 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQBAMAAADt3eJSAAAABGdBTUEAALGPC/xhBQAAAB5QTFRFAAAAqrfMvWxKJitEi5u00XbQ98KCwMvcm0yjPyYxhW+MwQAAAAF0Uk5TAEDm2GYAAABoSURBVAjXTc2xCYBADAXQa28ewREOF7CwViKWVjkX0KQTQcnf1gQbUz1+Qn5KGThTDPApQwQImH3KcKgvs/U+6rgVsCGSQjRFgtKMbdzgmXlB/NsLdZ6AhLkSfpCLeZOAHas6vJSrV7xSOjc2m/JhPQAAAABJRU5ErkJggg==', 'exit': 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQAgMAAABinRfyAAAABGdBTUEAALGPC/xhBQAAAAxQTFRFJitEUmB8wMvci5u0B/iEqQAAACpJREFUCNdj4P7//z8D9z8gwbd61SoG1tDQUAaIGIjgW0WE2G+Q2DqIGADp2iSBTJ449gAAAABJRU5ErkJggg=='}


def _demo():
    """Check the installation using the supplied state, without an engine solution."""
    from gridworld.controllers.pygame_input import PygameInput

    path = Path(__file__).resolve().parents[2] / "initial_state.json"
    state = json.loads(path.read_text(encoding="utf-8"))
    state["message"] = "Static preview · the engine is not implemented yet."
    view = PygameRender()
    source = PygameInput(view)
    view.start()
    try:
        view.update_render(state)
        while source.read_key() not in ("Escape", ":quit"):
            pass
    except KeyboardInterrupt:
        pass
    finally:
        view.close()


if __name__ == "__main__":
    _demo()
