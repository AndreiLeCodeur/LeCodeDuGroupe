"""Student entry point: uv run python -m gridworld --render terminal|pygame."""
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Grid-world — application assembly to implement in S0")
    parser.add_argument("--render", choices=["terminal", "pygame"], default="terminal",
                        help="display mode (default: terminal)")
    parser.add_argument("--level", default="levels/n0.json",
                        help="JSON map path (default: levels/n0.json)")
    args = parser.parse_args()
    # TODO: load Level, select InputSource and Renderer, then create Controller and Engine.
    # Start the renderer, call engine.run(), and close it in a finally block.
    raise NotImplementedError(
        f"assemble the game ({args.render}, {args.level}). "
        "To check the supplied files: uv run python -m gridworld.views.pygame_render"
    )


if __name__ == "__main__":
    main()
