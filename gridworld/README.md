# S2-01 — connect the supplied browser renderer

Start from the branch containing your integrated, playable S0 game.
Use your S1 test environment; if pytest is missing, run `uv add --dev pytest`.

Copy gridworld/api_render.py and gridworld/web_support.py into your project.
If an adapter already exists, preserve it and merge these connections deliberately.
Complete only read_state and play_action in api_render.py. The entire server,
request validation, JSON envelope, revisions and dialogue transport are supplied
in web_support.py; you do not need to read or modify its implementation.

Add Flask with `uv add 'flask>=3.1,<4'`. Run
`uv run python -m gridworld.api_render --level levels/n0.json`.
Install Node.js 22 or later (with npm) to run the supplied renderer.
In the supplied web-renderer folder, run
`npm start -- --api http://127.0.0.1:8000` and open http://127.0.0.1:8080/.
Leave API connection empty to use the supplied proxy. No frontend edits needed.

Add tests/test_api_render.py, complete the one TODO test and run
`uv run python -m pytest tests/test_api_render.py`.
GET observes; POST requests one action. The state remains the engine's eight-field
JSON dictionary; the server wraps it for the renderer. Your existing engine rules
are reused, not reimplemented in HTTP. Do not call Engine.run() in web mode.
