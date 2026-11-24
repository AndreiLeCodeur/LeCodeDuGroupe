"""Student entry point: uv run python -m gridworld --render terminal|pygame."""

import argparse
from gridworld.models.level import Level 
from gridworld.engine import Engine
from gridworld.controllers.controller import Controller
from gridworld.controllers.terminal_input import TerminalInput
from gridworld.controllers.pygame_input import PygameInput
from gridworld.views.bash_render import BashRender #voir mael pour bashrender
from gridworld.views.pygame_render import PygameRender

def main() -> None:
    parser = argparse.ArgumentParser(description="Grid-world — application assembly to implement in S0")
    parser.add_argument("--render", choices=["terminal", "pygame"], default="terminal",
                        help="display mode (default: terminal)")
    parser.add_argument("--level", default="levels/n0.json",
                        help="JSON map path (default: levels/n0.json)")
    args = parser.parse_args()
    #carte - S0-02
    level = Level.load(args.level)
    
    #affichage du jeu - S0-04
    if args.render == "terminal":
        renderer = BashRender()
        input_source = TerminalInput()
    else:
        renderer = PygameRender()
        input_source = PygameInput(renderer)
    
    #controleur et moteur S0-03
    controller = Controller(input_source)
    engine = Engine(level=level, controller=controller, renderer=renderer)

    #execution
    renderer.start()
    try:
        # Lancement de la boucle principale du jeu
        engine.run()
    finally:
        renderer.close()

if __name__ == "__main__":
    main()
