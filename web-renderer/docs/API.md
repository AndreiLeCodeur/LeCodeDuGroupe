# S2 — API contract for the supplied web renderer

This is the student-facing contract for the Python `api_render` adapter in S2-01.
It describes the required behavior; it is not an API implementation. The complete browser renderer, its 2D/3D views, assets and HTTP client
are already provided.
Students do not edit HTML, CSS or JavaScript and do not write tests for the renderer.

The API serves one shared game per server process. Multiple browser clients observe
and control that same game. Separate player sessions, reset, WebSockets and SSE
are outside this issue.

## Data flow and responsibilities

```text
Supplied browser controls
  -> game action (for example, "east")
  -> POST /api/actions
  -> student Python API
  -> Engine.apply_action(action)
  -> Engine.get_state()
  -> HTTP response containing a StateFrame
  -> supplied browser client
  -> supplied renderer.updateRender(state)
```

The browser also polls `GET /api/state`. The Python API answers requests; it does
not make an HTTP request to the browser or call a JavaScript method itself.
Changing the 2D/3D view, zoom or grid visibility is handled inside the supplied
renderer and sends no game action.

The existing Python `Controller` translates raw keys into actions for terminal
and Pygame input. The supplied browser client already performs this translation.
HTTP handlers receive actions, not keys, and delegate directly to the engine.
They are the controller adapter for web mode; a new key-reading Controller is not
required. Do not translate an action back into a key to reuse the local controller.

In web mode, HTTP requests drive game actions. Do not also run `Engine.run()` or a
terminal/Pygame input loop against the same game. Keep local modes working with
their existing controller and renderer. Arrange web-mode assembly without adding
HTTP dependencies or graphics rules to the game models.

`api_render` names the Python HTTP adapter here. It is not the graphical renderer,
and implementing the JavaScript drawing interface is not part of the assignment.
No additional public Python class signature is imposed by this contract.

## Successful response: StateFrame

Both endpoints return a JSON object with exactly these fields:

| Field | Type | Meaning |
|---|---|---|
| `protocol_version` | Integer, exactly `1` | Version of this HTTP envelope |
| `session_id` | Non-empty string | Created at server startup; changes after a server restart |
| `revision` | Non-negative integer | Starts at `0`; increases by one when the published state or `running` changes |
| `running` | Boolean | Whether the game still accepts actions |
| `state` | Object | The unmodified JSON-serializable result of `Engine.get_state()` |

A revision is independent of the turn counter. A blocked move changes the turn,
so it changes the revision. A move after victory changes neither. `quit` changes
`running` and the revision without changing the game state or turn.

`session_id` identifies the server instance, not a player or browser login.
Transport metadata stays outside the game state.

Return `Content-Type: application/json` and `Cache-Control: no-store` for successful
state responses.

## Game state: preserve the current Python contract

The authoritative references are `gridworld/contracts.py` and
`initial_state.json`. The current game state contains these eight fields:

- `level`: `id`, `width`, `height` and `tiles[y][x]`.
- `entities`: dictionaries with `id`, `kind`, `x`, `y` and `appearance`.
- `player_id`: identifies the player in `entities`.
- `status`: `playing` or `won` for N0; `lost` is reserved by the existing type.
- `turn`: a non-negative integer.
- `message`: initially empty; exactly `Victory!` on reaching the exit.
- `interaction`: `null` for N0.
- `extras`: `{}` for the base game.

The current state has no root `player` field and no `schema_version` field.
Do not add either to satisfy an older prototype. Do not move `entities` into
`extras`, duplicate the player position, or add graphical coordinates and asset paths.
The supplied renderer must consume this existing contract. `protocol_version` is
part of the HTTP envelope only.

Coordinates start at the top-left: east increases x, south increases y.
Each response contains a complete state, not a partial update. Numeric integer
fields do not accept booleans or numeric strings. Use ordinary JSON data; do not
emit NaN, infinity or Python objects.

An initial response for N0 is shown below.

```json
{
  "protocol_version": 1,
  "session_id": "example-server-session",
  "revision": 0,
  "running": true,
  "state": {
    "level": {
      "id": "n0",
      "width": 7,
      "height": 5,
      "tiles": [
        [
          "wall",
          "wall",
          "wall",
          "wall",
          "wall",
          "wall",
          "wall"
        ],
        [
          "wall",
          "floor",
          "floor",
          "wall",
          "floor",
          "exit",
          "wall"
        ],
        [
          "wall",
          "floor",
          "floor",
          "wall",
          "floor",
          "floor",
          "wall"
        ],
        [
          "wall",
          "floor",
          "floor",
          "floor",
          "floor",
          "floor",
          "wall"
        ],
        [
          "wall",
          "wall",
          "wall",
          "wall",
          "wall",
          "wall",
          "wall"
        ]
      ]
    },
    "entities": [
      {
        "id": "player-1",
        "kind": "player",
        "x": 1,
        "y": 1,
        "appearance": "player"
      }
    ],
    "player_id": "player-1",
    "status": "playing",
    "turn": 0,
    "message": "",
    "interaction": null,
    "extras": {}
  }
}
```

## GET /api/state

No request body is needed.

- Return `200 OK` and the current complete `StateFrame`.
- Reading state applies no action, consumes no turn and does not increase revision.
- The initial frame must exist before the first successful response.
- If the engine is not ready, return `503` with the error structure below.
- After `quit`, keep returning the last state with `running=false`.

Example request:

```sh
curl http://127.0.0.1:8000/api/state
```

Port 8000 is an example. Document the actual startup command and API address.

## POST /api/actions

Require `Content-Type: application/json`. The body must be an object containing
exactly one field, `action`, with a supported string value:

```json
{"action": "east"}
```

Supported actions: `north`, `east`, `south`, `west`, `wait`, `quit`.

Validate the request before changing the game. For a valid request while running,
process its action once and return `200 OK` with the resulting `StateFrame`.
Success means processing is complete; a `202` queue acknowledgement is not sufficient.

| Request | Expected result |
|---|---|
| Free movement while playing | Move and consume one turn; increase revision |
| Blocked movement while playing | Keep position, consume one turn; increase revision; return `200` |
| `wait` while playing | Keep position, consume one turn; increase revision |
| Reach the exit | Set `status="won"` and `message="Victory!"`; retain `running=true` |
| Movement or `wait` after victory | Return `200`; state, turn and revision remain unchanged |
| `quit` while running | Set `running=false`; increase revision; preserve the entire game state |
| A valid action after shutdown, including another `quit` | Return `409`; change nothing |
| Unknown action or invalid request shape | Return `422`; change nothing |

The API rejects further actions when `running=false`, even if calling the engine
alone would not enforce that transport rule. `quit` ends game control, not the HTTP
server. Send its response and keep the last frame readable until explicit server shutdown.

Example request:

```sh
curl -X POST http://127.0.0.1:8000/api/actions \
  -H 'Content-Type: application/json' \
  -d '{"action":"east"}'
```

Do not automatically retry POST requests: an action may already have been applied
even if its response was lost. Two separately received valid POSTs are two requests;
this contract does not provide deduplication of client retries.

## Errors

All errors return a JSON object in this form, with a stable code and readable
English message:

```json
{"error": {"code": "invalid_action", "message": "Unknown action: teleport"}}
```

| HTTP status | Error code | Situation |
|---|---|---|
| `400` | `invalid_json` | Body cannot be parsed as JSON |
| `415` | `unsupported_media_type` | Content type is missing or is not JSON |
| `422` | `invalid_request` | JSON is not an object with exactly one string `action` field |
| `422` | `invalid_action` | The action string is outside the supported vocabulary |
| `409` | `game_closed` | A valid action is submitted after `running=false` |
| `503` | `engine_unavailable` | The engine is not ready to serve the request |
| `500` | `internal_error` | Unexpected server failure; do not expose a traceback to the browser |

Validate content type, JSON and request shape/action before attempting a mutation.
Rejected requests do not change state, turn, revision or running status.

## Consistency and browser integration

Serialize action processing. Capture the resulting state, running status and
revision as one coherent frame before another action can change the game.
Concurrent GET requests must never see a partially updated frame. A lock or a
single worker with completed-result handling is sufficient; no distributed system
or second game loop is required.

The supplied browser client handles action queuing, polling, stale responses,
disconnection indicators and calling `updateRender(state)`. It sends actions
sequentially and polls approximately every 100–200 ms, with at most one GET in flight.
It uses session IDs and revisions to avoid displaying older responses.

Follow the supplied launch instructions to configure its API base URL without
editing browser source. Prefer serving the provided static bundle and API from
the same origin. If the provided setup uses separate ports, allow only the documented
frontend origin and the necessary requests; support preflight when needed.

## What students verify

Write Python tests for their HTTP adapter using the framework's in-process test
client. Cover response structure, headers, validation, actions, revision rules,
consistent snapshots, victory and shutdown. Run the existing S1 regression suite.
These tests need no browser, WebGL, real network listener or LLM.

Manually play N0 through the supplied renderer as an integration demonstration:

1. From a fresh start, request `west`: stay at `(1, 1)`, turn `1`, revision `1`.
2. Read state repeatedly: the turn and revision stay unchanged.
3. Restart the server to obtain a fresh game and a new session ID. Play
   `east, south, south, east, east, east, north, north`: reach `(5, 1)` at turn `8`
   with `won` and `Victory!`.
4. Movement and waiting after victory leave state and revision unchanged.
5. Submit `quit`: state stays unchanged, `running=false`, revision increases once;
   subsequent valid actions return `409`, while GET still succeeds.

There are no student assignments or tests for HTML, CSS, JavaScript, Canvas,
Three.js, animation, visual layout, asset loading or the renderer's networking code.
Those components are provided and verified. A supplied-renderer defect
should be reported to the tutor rather than worked around by changing the game contract.
