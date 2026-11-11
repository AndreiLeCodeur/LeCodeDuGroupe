# Gridworld — supplied web renderer

A complete, local browser view for S2: a pixel-art 2D plan and an animated 3D
stone diorama showing the **same engine state**. All graphics, assets, controls
and networking are supplied. Students implement and test their Python HTTP API;
they do not edit or test this renderer.

No Python files or Python dependencies are needed to preview this folder.
All graphics and Three.js 0.180.0 are bundled locally; no CDN, account, npm install
or build step is required. Use a current browser with ES modules and import maps.
WebGL failure automatically selects the 2D view with an explanation.

## Try the teacher demo

Install Node.js 22 or later, then run from the repository root:

```sh
cd web-renderer
npm run demo
```

Open **http://127.0.0.1:8080/?demo=1**. The server binds only to loopback.
Use `npm run demo -- --port 8087` if port 8080 is occupied.

The separate `tools/demo-world.mjs` is a small teacher reference world, not the
student Python API. Its game rules run on the Node server, never in the browser.
All tabs share the demo game. Stop with Ctrl+C and restart for a fresh game.
There is intentionally no reset action in the published API contract.

Open **http://127.0.0.1:8080/preview.html** to feed fixtures directly to
`updateRender`: initial state, move, blocked move, victory, optional potion,
collection, a new level with open corners, unknown appearance and invalid state.
Preview controls report intentions without changing the fixture. No gameplay
API is used on this page; fixture and asset files are loaded from the static server.

## Connect the student Python API

Start the student's API using their documented command. In another terminal:

```sh
cd web-renderer
npm start -- --api http://127.0.0.1:8000
```

Open **http://127.0.0.1:8080/**. The supplied local server proxies `/api/state`,
`/api/actions`, `/api/answer` and `/api/cancel` to that address. Leave the page's **API connection** field empty:
requests use the page's origin and the proxy, so no CORS configuration is needed.
The proxy does not implement gameplay and never retries a POST.

Alternatively, serve `index.html`, `app.js`, `style.css`, `src/`, `assets/` and
`vendor/` from the API's own static server. Relative asset URLs also support a
frontend mounted under a subdirectory. The default API routes are origin-root
`/api/state` and `/api/actions`.

For separate origins without the proxy, expand **API connection**, enter the API
base URL and select **Connect**, or open `/?api=http://127.0.0.1:8000`.
Configure the Python server to allow the exact frontend origin (for example
`http://127.0.0.1:8080`), GET/POST and the Content-Type header, including OPTIONS
preflight. Do not open `index.html` using `file://`: modules and model loading need
HTTP. No browser source edits are needed for any of these options.

The full student contract is in [docs/API.md](docs/API.md), matching
[public project assignments](https://github.com/DavidBert/INSA-project-gridworld-starter/issues).
It is a copy of `project/docs/web-renderer-api.md`; keep both synchronized when
changing the published contract.

```text
GET  /api/state
POST /api/actions  {"action":"east"}

200 application/json, Cache-Control: no-store
{
  "protocol_version": 1,
  "session_id": "a-new-id-for-each-server-start",
  "revision": 0,
  "running": true,
  "state": { ...Engine.get_state()... }
}
```

The state has the existing eight fields: `level`, `entities`, `player_id`,
`status`, `turn`, `message`, `interaction`, `extras`. There is no root `player`
or `schema_version`. The renderer internally maps appearance `player` to
`player.idle`, and an exit tile to stairs. It never changes the received state.
See [fixtures/initial.json](fixtures/initial.json) for the complete example.

The browser polls every 150 ms after the previous read finishes, with at most
one GET in flight. POSTs are sequential. Revisions discard stale responses;
server session changes abort outstanding requests and require a fresh GET.
Disconnected clients retain the last image and disable game controls. Reads
retry after one second; an uncertain POST is **never replayed**. A closed game
remains visible and readable. Requests time out after five seconds.

## Controls

| Input | Intention or local setting |
|---|---|
| Arrow keys or Z Q S D, case-insensitive | North, west, south, east |
| Space / Wait | Wait |
| Escape / Quit | Quit |
| G / Grid | Toggle the local grid |
| Diorama / Plan | Change the view only |
| + / − / Fit | Local 3D zoom; Fit restores the full level |

Click the board or a game button to focus keyboard control. Each key press sends
one intention; key auto-repeat, modified shortcuts and typing in form fields are
ignored. Touch and keyboard-accessible buttons are supplied for every action.
The engine decides whether a move succeeds, consumes a turn or wins the game.
Changing view, grid or zoom sends no action. North is up and east is right in
both views; the camera never rotates or follows the player.

HUD values come from the state. The inventory appears only when
`extras.inventory` is an array. Optional potion entities belong in root `entities`,
not `extras.entities`. Collection is illustrated by two fixtures; it is not
implemented by the renderer or the base demo world. Unknown appearances get a
visible placeholder and diagnostic, never a guessed game rule or arbitrary URL.
The sphinx has supplied 2D and 3D artwork. Its dialogue panel reads the five
public `interaction` fields and supports question, pending, rejected, error and
accepted states. Movement is disabled while dialogue pauses the game; quit stays
available. Answers are trimmed and limited to 500 Unicode characters. Submission
expects HTTP 202 with a pending frame; later GETs show the verdict. Close dialogue
sends `/api/cancel` with the current interaction ID. The client never retries an
uncertain answer or cancellation. The supplied Python transport handles request
validation and obsolete results. Students implement the engine's victory rule.

After implementing S2-04, launch your Python API with the sphinx map and fake:

```sh
uv run python -m gridworld.api_render --level levels/sphinx.json --fake-sphinx accepted
```

Connect through the same proxy. On the simplified map, four attempted east moves
encounter the sphinx on the exit. Submit an answer: acceptance moves onto the exit
and wins immediately. Also try the `rejected` fake, which displays a hint and keeps
the player before the exit. Its verdict comes from the launch option, not the text.
Omit the flag for the real Sphinx after completing S2-03. The supplied launcher
prepares one riddle before starting HTTP. The older Node passage demo and sphinx
fixtures illustrate the renderer's broader capabilities, not additional student work.

See [docs/DIALOGUE.md](docs/DIALOGUE.md) for the dialogue transport contract and
the [S2 guide](https://davidbert.github.io/OutilsNumeriques/s2/) for project setup.

## Public renderer API

Include `style.css` and the import map before importing the module:

```html
<script type="importmap">
  {"imports":{"three":"./vendor/three.module.js"}}
</script>
<script type="module">
  import {GridWorldRenderer} from './src/renderer.js';
  const renderer = new GridWorldRenderer({view: '3d'});
  const unsubscribe = renderer.onAction(action => yourAdapter.send(action));
  await renderer.mount(document.querySelector('#game'));
  renderer.updateRender(yourState);
  // On teardown: unsubscribe(); renderer.dispose();
</script>
```

| Method | Behavior |
|---|---|
| `mount(element): Promise<void>` | Load assets and prepare both views; call once per instance |
| `updateRender(state): void` | Validate and copy the complete state; preserve the last good image on invalid input |
| `setView('2d' \| '3d'): void` | Display the latest state without an action |
| `setGridVisible(boolean): void` | Change a local preference |
| `onAction(callback): () => void` | Subscribe and receive an unsubscribe function |
| `setConnection(status): void` | Adapter hook: `local`, `connecting`, `connected`, `disconnected`, `closed` |
| `showError(message): void` | Display a safe-text transport diagnostic |
| `dispose(): void` | Remove owned DOM/listeners and release animation/WebGL resources; never close the engine |

Updates before or during `mount` retain only the latest valid state. A disposed
instance cannot be mounted again. `src/assets.js` owns asset loading;
`src/api-client.js` owns gameplay HTTP; drawing modules contain no fetch calls.
`preview.js` demonstrates using the renderer independently of HTTP gameplay.

Terrain is rebuilt only when its ID, dimensions or tile content changes.
Actors are keyed by ID; changes of level clear old actors, even for reused IDs.
Adjacent movement interpolates for 140 ms; resets, level changes and non-adjacent
jumps snap to the received position. Reduced motion removes interpolation and
ambient animation. Hidden tabs and the inactive 3D view suspend animation.
`dispose` releases generated resources and shared assets at their proper lifetimes.

## Teacher verification

```sh
npm test
```

These Node checks belong to the **supplied renderer**, not to the student task.
They cover state validation/copying, keyboard intent mapping, API response order,
server restarts, disconnection, no POST retry, shutdown, the reference world,
local assets and camera orientation. No npm dependencies are required.

Manual acceptance:

1. Start a fresh demo. West keeps `(1, 1)`, with turn 1.
2. Restart the demo. Play east, south, south, east, east, east, north, north:
   player `(5, 1)`, turn 8, `Victory!`. Wait leaves these values unchanged.
3. Switch views mid-game; toggle the grid and zoom. No new turn is consumed.
4. Quit retains the scene and disables actions. GET still works.
5. Stop the server: the scene remains, controls disable and the connection
   indicator changes. Restart: the new session starts at turn 0 without replaying
   a queued action.
6. In the fixture preview, select the new level: old entities disappear and the
   4 × 4 board is fitted, with no decorative columns on its open corners.
7. Check optional potion/collection, unknown appearance and invalid state.
8. Check at phone width and with reduced motion; confirm the entire map is
   reachable with Fit and all controls remain usable. Disable WebGL to check 2D
   fallback. Asset files must work with external internet access disabled.

## Folder and licenses

- `src/`: supplied presentation, state validation, input and network modules.
- `assets/`: manifests, Kenney sprites, GLB models and model textures.
- `vendor/`: local Three.js 0.180.0 modules and MIT license.
- `fixtures/`, `preview.*`: teacher examples for direct state updates.
- `tools/`: local static/proxy server and isolated teacher demonstration world.
- `tests/`: teacher maintenance checks; never student deliverables.
- `docs/API.md`: student API contract.

Kenney Mini Dungeon and Tiny Dungeon assets are CC0; original license files are
in `assets/models/License-Kenney.txt` and `assets/sprites/License-Kenney.txt`.
Three.js and its supplied loaders/utilities use the MIT license in `vendor/LICENSE`.
The visual composition adapts the teacher's `exemple-gridworld` prototype.
