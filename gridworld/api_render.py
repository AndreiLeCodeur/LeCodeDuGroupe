"""Complete only these two connections between HTTP and your existing engine."""
from gridworld.web_support import build_app, launch


def read_state(engine):
    """Return the current game state without advancing the game."""
    return engine.get_state()


def play_action(engine, action):
    """Apply one action, then return the updated game state."""
    engine.apply_action(action)
    return engine.get_state()


def create_app(engine):
    return build_app(engine, read_state, play_action)


if __name__ == "__main__":
    launch(create_app)
