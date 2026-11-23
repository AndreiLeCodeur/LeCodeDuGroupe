"""Supplied finite scenarios on the real engine, without UI or real LLM."""
import json
from pathlib import Path

from gridworld.controllers.controller import Controller
from gridworld.engine import Engine


class UnusedInput:
    def read_key(self):
        raise AssertionError("Scenarios use actions, not keyboard input")


class NoDisplay:
    def start(self):
        return None

    def update_render(self, state):
        return None

    def close(self):
        return None


def play_scenario(level, path: Path):
    """Return the final public state; the student test decides whether it won."""
    if not path.is_file():
        raise AssertionError(f"Missing scenario: {path}")
    steps = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(steps, list) or not steps:
        raise AssertionError(f"{path}: expected a non-empty list of steps")
    engine = Engine(level, Controller(UnusedInput()), NoDisplay())
    if level.get_sphinx() is not None:
        from gridworld.web_support import FakeSphinx
        engine.sphinx = FakeSphinx("accepted")
        engine.sphinx.get_question()
    for number, step in enumerate(steps, 1):
        if isinstance(step, str):
            if step not in ("north", "east", "south", "west", "wait"):
                raise AssertionError(f"{path}, step {number}: unknown action {step!r}")
            engine.apply_action(step)
        elif isinstance(step, dict) and set(step) == {"answer"}:
            if not isinstance(step["answer"], str) or not step["answer"].strip():
                raise AssertionError(f"{path}, step {number}: answer must be non-empty text")
            if engine.get_state()["interaction"] is None or engine.sphinx is None:
                raise AssertionError(f"{path}, step {number}: no active sphinx dialogue")
            engine.apply_sphinx_verdict(engine.sphinx.answer(step["answer"]))
        else:
            raise AssertionError(f"{path}, step {number}: invalid scenario step")
    return engine.get_state()