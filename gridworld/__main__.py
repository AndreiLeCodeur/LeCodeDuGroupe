"""Student entry point: uv run python -m gridworld --render terminal|pygame."""

import argparse

from gridworld.controllers.controller import Controller
from gridworld.controllers.terminal_input import TerminalInput
from gridworld.engine import Engine  # Ou la classe Engine selon votre arborescence
from gridworld.models.level import (  # Adapter selon le nom de votre module de chargement de niveau
    Level,
)
from gridworld.views.bash_render import BashRender
from gridworld.views.pygame_input import PygameInput
from gridworld.views.pygame_render import PygameRender


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Grid-world — application assembly to implement in S0"
    )
    parser.add_argument(
        "--render",
        choices=["terminal", "pygame"],
        default="terminal",
        help="display mode (default: terminal)",
    )
    parser.add_argument(
        "--level",
        default="levels/n0.json",
        help="JSON map path (default: levels/n0.json)",
    )
    args = parser.parse_args()

    # 1. Chargement du niveau
    # Si votre classe utilise Level.from_json_file, load_level ou Level(args.level),
    # ajustez l'appel ci-dessous selon contracts.py / models/
    level = Level.load(args.level)

    # 2. Sélection du renderer et de la source d'entrée selon l'argument
    if args.render == "pygame":
        renderer = PygameRender()
        input_source = PygameInput(renderer)
    else:
        renderer = BashRender()
        input_source = TerminalInput()

    # 3. Création du contrôleur et du moteur
    controller = Controller(input_source)
    engine = Engine(level=level, controller=controller, renderer=renderer)

    # 4. Cycle de vie : démarrer le renderer, lancer la boucle de jeu, puis fermer dans un bloc finally
    renderer.start()
    try:
        engine.run()
    finally:
        renderer.close()


if __name__ == "__main__":
    main()
