"""Supplied HTTP plumbing. No student changes are required in this module."""
import argparse
from copy import deepcopy
from threading import RLock, Thread
from uuid import uuid4

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException


class RequestError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message


def new_interaction(sphinx):
    """The riddle is prepared at startup; this reads its cached question."""
    return {"id": uuid4().hex, "actor_id": "sphinx-1", "status": "question",
            "question": sphinx.get_question(), "message": ""}


class FakeSphinx:
    """Supplied deterministic sphinx for integration, without Ollama."""
    def __init__(self, outcome="accepted"):
        self.outcome = outcome
        self.history = []

    def get_question(self):
        return "What repeats your words without a mouth?"

    def answer(self, text):
        correct = self.outcome == "accepted"
        message = "Correct!" if correct else "Think about a sound returning."
        if correct:
            self.history.clear()
        else:
            self.history.append({"answer": text, "hint": message})
        return {"correct": correct, "message": message}


def build_app(engine, read_state, play_action):
    app = Flask(__name__)
    lock = RLock()
    session_id, revision, attempt = uuid4().hex, 0, None

    def frame():
        return {"protocol_version": 1, "session_id": session_id,
                "revision": revision, "running": engine.running,
                "state": deepcopy(read_state(engine))}

    def body(fields):
        if not request.is_json:
            raise RequestError(415, "unsupported_media_type", "Send application/json")
        try:
            data = request.get_json()
        except HTTPException:
            raise RequestError(400, "invalid_json", "Send valid JSON")
        if not isinstance(data, dict) or set(data) != set(fields) or any(
                not isinstance(data[key], str) for key in fields):
            raise RequestError(422, "invalid_request", "Check the request fields")
        return data

    def active():
        if not engine.running:
            raise RequestError(409, "game_closed", "The game is closed")

    def dialogue(data):
        active()
        interaction = getattr(engine, "interaction", None)
        if not interaction or interaction["id"] != data["interaction_id"]:
            raise RequestError(409, "stale_interaction", "This dialogue is no longer active")
        return interaction

    @app.after_request
    def no_cache(response):
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.errorhandler(RequestError)
    def request_error(error):
        return jsonify(error={"code": error.code, "message": error.message}), error.status

    @app.errorhandler(Exception)
    def internal_error(error):
        if isinstance(error, HTTPException):
            return jsonify(error={"code": "http_error", "message": error.name}), error.code
        app.logger.exception("Game request failed")
        return jsonify(error={"code": "internal_error", "message": "Check the Python terminal"}), 500

    @app.get("/api/state")
    def get_state():
        with lock:
            return jsonify(frame())

    @app.post("/api/actions")
    def post_action():
        nonlocal revision, attempt
        action = body(["action"])["action"]
        if action not in ("north", "east", "south", "west", "wait", "quit"):
            raise RequestError(422, "invalid_request", "Unknown action")
        with lock:
            active()
            before = (deepcopy(read_state(engine)), engine.running)
            play_action(engine, action)
            if action == "quit":
                attempt = None
                engine.interaction = None
            if (read_state(engine), engine.running) != before:
                revision += 1
            return jsonify(frame())

    def evaluate(token, interaction_id, sphinx, answer):
        nonlocal revision, attempt
        try:
            verdict = sphinx.answer(answer)
            if (not isinstance(verdict, dict) or set(verdict) != {"correct", "message"}
                    or type(verdict["correct"]) is not bool
                    or not isinstance(verdict["message"], str)):
                raise ValueError("Invalid verdict")
        except Exception:
            verdict = None
        with lock:
            current = getattr(engine, "interaction", None)
            if (attempt != token or not engine.running or not current
                    or current["id"] != interaction_id):
                return
            try:
                if verdict is None:
                    raise RuntimeError("Evaluation unavailable")
                engine.apply_sphinx_verdict(verdict)
                engine.sphinx = sphinx
            except Exception:
                engine.interaction = current
                current.update(status="error", message="The evaluator is unavailable. Try again.")
            attempt = None
            revision += 1

    @app.post("/api/answer")
    def post_answer():
        nonlocal revision, attempt
        data = body(["interaction_id", "answer"])
        answer = data["answer"].strip()
        if not 1 <= len(answer) <= 500:
            raise RequestError(422, "invalid_request", "Use 1 to 500 characters")
        with lock:
            current = dialogue(data)
            if current["status"] == "pending":
                raise RequestError(409, "evaluation_pending", "Please wait")
            if current["status"] not in ("question", "rejected", "error"):
                raise RequestError(409, "interaction_complete", "The dialogue is complete")
            # A private copy keeps cancelled/obsolete work out of the live history.
            working_sphinx = deepcopy(engine.sphinx)
            previous = deepcopy(current)
            token = uuid4().hex
            attempt = token
            current.update(status="pending", message="")
            revision += 1
            pending_frame = frame()
            worker = Thread(target=evaluate, args=(token, current["id"], working_sphinx, answer), daemon=True)
            try:
                worker.start()
            except Exception:
                engine.interaction = previous
                attempt = None
                revision -= 1
                raise
            return jsonify(pending_frame), 202

    @app.post("/api/cancel")
    def post_cancel():
        nonlocal revision, attempt
        data = body(["interaction_id"])
        with lock:
            dialogue(data)
            attempt = None
            engine.interaction = None
            revision += 1
            return jsonify(frame())

    return app


def launch(create_app):
    from gridworld.controllers.controller import Controller
    from gridworld.controllers.terminal_input import TerminalInput
    from gridworld.engine import Engine
    from gridworld.models.level import Level
    from gridworld.views.bash_render import BashRender

    parser = argparse.ArgumentParser(description="Run the supplied browser adapter")
    parser.add_argument("--level", default="levels/n0.json")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--fake-sphinx", choices=("accepted", "rejected"))
    args = parser.parse_args()
    level = Level.load(args.level)
    engine = Engine(level, Controller(TerminalInput()), BashRender())
    # This branch becomes active when the S2-04 engine has a sphinx attribute.
    if hasattr(engine, "sphinx") and level.get_sphinx() is not None:
        if args.fake_sphinx:
            engine.sphinx = FakeSphinx(args.fake_sphinx)
        else:
            from gridworld.sphinx import Sphinx
            engine.sphinx = Sphinx()
        print("Preparing the sphinx question...", flush=True)
        try:
            engine.sphinx.get_question()
        except Exception as error:
            raise SystemExit("Cannot prepare the riddle. Check Ollama or use --fake-sphinx accepted.") from error
    create_app(engine).run(host="127.0.0.1", port=args.port, threaded=True, use_reloader=False)
