


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

## Play in the browser

The supplied web renderer talks to the engine through a small HTTP API.
It needs Node.js 22 or later (check with `node --version`).

In a first terminal, from the repository root, start the Python API (port 8000):

```sh
uv run python -m gridworld.api_render --level levels/n0.json
```

In a second terminal, from the `web-renderer/` folder, start the renderer (port 8080):

```sh
npm start -- --api http://127.0.0.1:8000
```

Open http://127.0.0.1:8080/ and leave "API connection" empty: the renderer
forwards `/api` requests to Python.

`GET /api/state` only observes the game and never changes it, while
`POST /api/actions` asks the engine to play one action and returns the new state.

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


# S2-03 — service d'évaluation du sphinx

`gridworld/sphinx_service.py` fournit au moteur un petit service qui crée une énigme et juge la réponse d'un joueur. Le moteur dépend uniquement du protocole `SphinxService` (`create_riddle()` et `judge()`) : il ne sait pas si c'est Ollama ou un double de test qui répond.

- `FakeSphinxService(outcome)` : sans modèle ni réseau. Le résultat est choisi à l'avance (`accepted`, `rejected`, `timeout`, `unavailable` ou `invalid`) et ne dépend jamais du texte du joueur.
- `OllamaSphinxService(url, model, timeout)` : appelle un serveur Ollama local, sur CPU (`num_gpu=0`). Aucune requête n'est envoyée à la construction de l'objet.

Une mauvaise réponse et une panne technique sont deux situations différentes. Une mauvaise réponse donne `Verdict(accepted=False, ...)`. Une panne lève `ServiceTimeout`, `ServiceUnavailable` ou `InvalidServiceResponse` (toutes héritent de `ServiceError`), pour que le jeu puisse proposer une nouvelle tentative au lieu d'annoncer que le joueur s'est trompé. Le client vérifie strictement les types : `"accepted": "false"` est refusé, car `bool("false")` vaut `True`.

La réponse de référence reste côté serveur. Elle est masquée dans `repr()`, mais pas dans `asdict()` ni dans un JSON : elle ne doit donc jamais être copiée dans l'état public du jeu ni dans `Verdict.message`.

## Configuration

Les valeurs par défaut sont définies dans `gridworld/sphinx_service.py` :

| Paramètre | Valeur par défaut |
|---|---|
| URL | `http://127.0.0.1:11434` |
| Modèle | `qwen2.5:1.5b-instruct-q4_K_M` |
| Délai maximal | `180` secondes (fini et positif ; le premier appel peut inclure le chargement du modèle) |

## Lancer les tests

Les tests sont hors ligne : ils ne démarrent jamais Ollama, ne chargent aucun modèle et ne contactent aucun serveur réseau.

```bash
uv run python -m pytest tests/test_sphinx_service.py -q
uv run python -m pytest -q
```

## Lancer l'évaluation manuelle (vrai modèle)

Cette étape est séparée des tests et n'est jamais exécutée par pytest.

1. Installer Ollama (https://ollama.com/download) et le laisser tourner. `http://127.0.0.1:11434` doit afficher « Ollama is running » ; sinon, lancer `ollama serve` dans un autre terminal.
2. Télécharger le modèle une seule fois (les poids ne sont pas stockés dans Git) :
   ```bash
   ollama pull qwen2.5:1.5b-instruct-q4_K_M
   ```
3. Depuis la racine du dépôt, lancer l'évaluation sur une seule ligne :
   ```bash
   uv run python -m gridworld.evaluate_sphinx --riddle levels/sphinx.json --corpus docs/sphinx/evaluation-corpus.json --output sphinx-evaluation.json --cpu-note "CPU, RAM, version d'Ollama, ce que montre ollama ps"
   ```
4. Pendant l'exécution, ouvrir un autre terminal et lancer `ollama ps`. La colonne `PROCESSOR` indique l'utilisation CPU réellement observée. Demander `num_gpu=0` et observer `100% CPU` sont deux informations différentes.

`--url`, `--model` et `--timeout` permettent de changer la configuration sans toucher au moteur. `--notes` ajoute une courte interprétation au rapport.

### Ce que fait le script

- Il n'envoie au modèle que les cas `accepted`, `rejected` et `ambiguous`. Les cas de validation HTTP, de panne simulée et d'annulation sont vérifiés dans S2-04.
- Les réponses sont nettoyées (`strip()`) avant d'être jugées, comme le fait l'API.
- Si `levels/sphinx.json` ne contient pas d'énigme, l'énigme fixe du corpus est utilisée.
- Chaque cas enregistre la réponse, le résultat attendu, le verdict ou le nom de l'erreur, et la durée mesurée avec `perf_counter()`.
- Une panne du service est enregistrée comme `service_error` et n'est jamais comptée comme une réponse refusée.
- Les cas ambigus sont enregistrés mais restent hors du score binaire.

### Le rapport (`sphinx-evaluation.json`)

Il contient le matériel, la version de Python, le modèle, les options, le délai maximal, les durées (premier appel et appels suivants), le résultat de chaque cas et une courte interprétation. Chaque cas est classé `correct`, `false_positive` (mauvaise réponse acceptée), `false_negative` (bonne réponse refusée), `ambiguous` ou `service_error`.

Le rapport décrit les résultats et les limites : réponses exactes, paraphrases, mauvaises réponses et tentatives de modifier la consigne. Un JSON valide ne garantit pas un jugement juste, et un petit corpus (une énigme, un essai par cas) ne prouve pas que le modèle est fiable. Séparer la consigne (message `system`) du texte du joueur (message `user`) aide, mais ne garantit pas la résistance à toutes les tentatives de contournement.