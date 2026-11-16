# Supplied sphinx dialogue

The simplified S2 exercise uses the existing browser panel without frontend edits.
The Python transport is now supplied in `gridworld/web_support.py`; students
implement the Sphinx conversation and the engine's game rules only.

`state.interaction` is null outside dialogue. Otherwise it contains exactly five
strings: `id`, `actor_id`, `status`, `question`, `message`. The actor exists in
`entities` with kind/appearance `sphinx`. The sphinx stands on the exit.
Never serialize the private reference answer or history as public state fields.

| Request | Body | Response |
| --- | --- | --- |
| GET /api/state | None | 200, complete StateFrame |
| POST /api/answer | `{"interaction_id":"current-id","answer":"player text"}` | 202, complete pending StateFrame |
| POST /api/cancel | `{"interaction_id":"current-id"}` | 200, interaction=null |

The supplied transport validates JSON, ID and 1–500 characters of answer text,
runs evaluation outside the game lock, and ignores obsolete work after cancel
or quit. It uses a private conversation copy during evaluation, committing it
only when the current attempt still matches. GET remains available while waiting.
These mechanisms are provided, not student deliverables.

| Status | Panel |
| --- | --- |
| question | Question and answer form |
| pending | Waiting, disabled answer input, cancellation available |
| rejected | Model-generated hint and another attempt |
| error | Supplied technical-failure message and another attempt |
| accepted | Supported for the older passage demo; not needed for the simplified exit game |

For the simplified game, success immediately moves the player onto the exit,
sets game status to won, clears interaction and displays Victory!. The boolean
verdict is named `correct` in the Sphinx Python interface; it is not an additional
public interaction field. Failed verdict messages are displayed as hints, as
requested by the course. The prompt asks not to reveal the answer, but no claim
is made that a model-generated hint is always appropriate or private.

Encounter consumes one turn; answers and cancellation consume none. Movement is
paused while dialogue is active. The question is generated once and cached; the
supplied launcher prepares it before starting HTTP. Successful answers clear the
Sphinx history. Closing the panel preserves the riddle and committed attempts.

The older supplied Node demo still demonstrates a sphinx guarding a passage,
with an accepted state followed by movement. It is a renderer demo, not the
required simplified student game. Both forms use the same browser wire format.
