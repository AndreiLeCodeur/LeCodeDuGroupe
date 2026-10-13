


# Gridworld starter

A small Python grid-world project built during class. The code contains skeletons
to complete and a supplied Pygame preview that works from the start.

## Get started

Fork this repository for your group, then clone your fork:

```sh
git clone https://github.com/YOUR-GROUP/YOUR-REPO.git
cd YOUR-REPO
```

Use Python 3.12 and [uv](https://docs.astral.sh/uv/getting-started/installation/).
Install the dependencies and open the preview:

```sh
uv sync --locked
uv run python -m gridworld.views.pygame_render
```

The preview displays a fixed map. Close it with Escape or the window close
button. The playable game is not implemented yet; unfinished methods raise
`NotImplementedError`.

When opening a pull request, select your group's fork as the base repository.

## Run the tests

`uv sync --locked` also installs pytest (development dependency). Run the
whole suite from the repository root:

```sh
uv run python -m pytest -q
```

The command exits with status 0 when every test passes and non-zero otherwise.
Tests need no window, keyboard or network.

Shared fixtures live in [`tests/conftest.py`](tests/conftest.py) and are
created fresh for each test:

| Fixture | Provides |
| --- | --- |
| `level_data` | A small 5×3 level as a dict (same format as `levels/n0.json`). |
| `level` | A `Level` built from `level_data`. |
| `renderer` | A `RecordingRenderer` that stores every received state in `renderer.states`. |
| `make_game` | A function: `make_game(["d", "d"])` returns an `Engine` fed with those keys. |
| `game` | An `Engine` with no scripted keys, for calling `apply_action` directly. |

The test doubles are in [`tests/helpers.py`](tests/helpers.py).
`ScriptedInput` raises an `AssertionError` if the engine asks for more keys
than scripted, so a test fails instead of looping forever.

## Repository tour

| Path | What you will find |
| --- | --- |
| [`gridworld/models/`](gridworld/models/) | Skeletons for tiles, the level and the player. |
| [`gridworld/engine.py`](gridworld/engine.py) | Skeleton for game rules and the game loop. |
| [`gridworld/controllers/`](gridworld/controllers/) | Keyboard input sources and the controller that translates keys into actions. |
| [`gridworld/views/`](gridworld/views/) | Terminal rendering skeleton and supplied Pygame view. |
| [`gridworld/contracts.py`](gridworld/contracts.py) | Shared data formats and interfaces between components. |
| [`gridworld/__main__.py`](gridworld/__main__.py) | Command-line entry point, with rendering and level arguments already declared. |
| [`levels/n0.json`](levels/n0.json) | The starting map: terrain, player start and exit coordinates. |
| [`tests/`](tests/) | Pytest suite, shared fixtures and test doubles. |
| [`initial_state.json`](initial_state.json) | Example of the game state passed to a view. |
| [`pyproject.toml`](pyproject.toml), [`uv.lock`](uv.lock), [`.python-version`](.python-version) | Dependencies and Python version used by the project. |

The engine applies game rules, the controller translates input, and the views
show the resulting state.

`PygameRender`, `PygameInput` and `BashRender.refresh` are supplied. The Pygame
sprites are embedded, so no separate asset download is needed.

## Contributors

Andrei Glavan
Henry Chollet
Robin Blondeau
Maël Cunin
Guillem JIMENEZ
Ferdinand Pitré
Thomas Vilatte

## Credits

Sprites: [Kenney Tiny Dungeon](https://kenney.nl/assets/tiny-dungeon), CC0.
