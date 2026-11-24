# S4 common kit — one setup PR per group

Supplied: an additive terminal adapter, updated Pygame/web views, a gallery, shared
contracts, deterministic test doubles and unimplemented component signatures.
The deliberately inconsistent legacy enemies are supplied to refactor.
This kit does NOT implement the common enemy classes, star, factory or game integration.
No engine, model, BashRender, root contracts.py, dependency file or existing test is replaced.

## Install after the practical

1. One volunteer pair starts a branch from the group's current dev (or DEV).
   Everyone else completes the practical in a separate folder.
2. Extract the ZIP into a temporary directory. Read S4-FILES.json. Compare the
   existing Pygame view before updating it; preserve any local additions.
3. Copy gridworld/s4/ beside your existing modules, and testing/ at the project
   root. If either already exists, compare/merge; never overwrite student work.
4. Keep gridworld/views/bash_render.py unchanged. Copy the supplied
   gridworld/views/s4_bash_render.py beside it, and update pygame_render.py
   after comparison. In your existing terminal launcher (normally
   gridworld/__main__.py), replace its BashRender import with:

   ```python
   from gridworld.views.s4_bash_render import S4BashRender as BashRender
   ```

   Keep the existing `BashRender()` construction and game logic. If the import
   is inside a terminal-only function, keep it there. This supplied subclass
   delegates old frames to your original renderer and adds S4 appearances when
   needed. Copy preview_s4.py and s4-preview/ to the project root.
5. Copy the CONTENTS of web/ into your existing supplied frontend directory:
   web/ for the S2 practical convention, or web-renderer/ if that is what your
   launcher uses. Keep your API launch command and configured frontend path.
   This complete supplied frontend includes its licenses, local assets and
   tools/serve.mjs proxy. Existing npm start -- --api commands remain usable.
6. Run the existing project's tests. Launch your old map with your normal
   terminal/Pygame/API commands. Its behavior must remain unchanged.
7. From the project root, preview new appearances without S4 game code:
   `uv run python preview_s4.py --render terminal` (Enter between snapshots), or
   `uv run python preview_s4.py --render pygame` (Space / Escape).
   For the web gallery: `uv run python -m http.server 8005 --bind 127.0.0.1 --directory web`
   and open http://127.0.0.1:8005/preview.html. Substitute your actual frontend
   folder in that command. Check both 2D and 3D, then Ctrl+C.
8. Commit the supplied files, open the setup PR into dev, review and merge.
   Other pairs update dev before creating their feature branches.

Do not copy the practical's gridworld/, pyproject.toml, uv.lock, s4_lab/ or tests/
over your game. The common kit contains no replacement project configuration.
Pygame was installed in S0; keep your dependencies and launcher behavior.
Only the terminal renderer import changes; your S2 API setup stays unchanged.
Do not connect unfinished S4 components to Engine during setup. Their TODOs
raise NotImplementedError deliberately; imports alone should not break S0–S3.

## Visual contract

Use appearances enemy.horizontal (H), enemy.vertical (V), enemy.chaser (C),
actor.fake (F), star (*), player and player.invincible (@ / golden halo).
Set extras.invincible_turns while positive; omit the key at zero to preserve
old snapshots. The supplied HUD defaults to zero.
An invisible star is absent from the public entities array but remains in the
actor collection. An eliminated enemy is removed from both. Keep the player last.
No rendering changes are required in the feature PRs.

## Parallel work

- PR 1: gridworld/s4/enemies.py and its own test file. Read the supplied
  legacy_enemies.py; testing/s4_reference.py lets you compare old/new traces.
- PR 2: star.py, invincibility.py and their tests.
- PR 3: factory.py and loader tests using testing/s4-room.json. Keep this map
  outside levels/ until final integration; it has a matching supplied scenario. Inject recording
  constructors from testing.s4_fakes; do not wait for unfinished concrete classes.
- PR 4: turn_system.py and tests using FakeWorld, FakeActor, FixedRandom and
  FakeInvincibility. These are simple supplied classes, not a mocking framework.
- Final integration PR: connect the loader, player effect and phase to Engine;
  use the real classes together and keep the S1/S2 tests passing.

ActorWorld is supplied for the real occupancy checks; keep its actor list shared
when eliminating enemies (see CONTRACT.md). The Protocol is supplied; do not independently rename its methods. Read
`gridworld/s4/CONTRACT.md` before implementation. The detailed S4 project issues
specify behaviors; this kit is the shared starting point, not those issues.
