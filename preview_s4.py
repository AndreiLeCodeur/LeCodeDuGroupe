"""SUPPLIED: preview S4 snapshots without completing any exercise."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--render", choices=("terminal", "pygame"), default="terminal")
args = parser.parse_args()
if args.render == "pygame":
    from gridworld.views.pygame_render import PygameRender
    from gridworld.controllers.pygame_input import PygameInput
    view = PygameRender()
    source = PygameInput(view)
else:
    from gridworld.views.s4_bash_render import S4BashRender
    view = S4BashRender()
try:
    view.start()
    for name in ("visible", "hidden", "invincible", "lost"):
        state = json.loads((Path(__file__).parent / "s4-preview" / f"{name}.json").read_text())
        view.update_render(state)
        if args.render == "terminal":
            input("Enter: next snapshot > ")
        else:
            while (key := source.read_key()) != " ":
                if key == "Escape":
                    raise SystemExit
finally:
    view.close()
