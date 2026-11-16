"""Engine and HTTP integration tests: no browser, live server or LLM."""
from threading import Event
import time
import unittest

from gridworld.api_render import create_app
from gridworld.controllers.controller import Controller
from gridworld.controllers.terminal_input import TerminalInput
from gridworld.engine import Engine
from gridworld.models.level import Level
from gridworld.views.bash_render import BashRender
from gridworld.web_support import FakeSphinx


class BlockingSphinx:
    """Double contrôlable qui bloque l'évaluation jusqu'à release.set()."""
    def __init__(self, verdict: dict | None = None) -> None:
        self.started = Event()
        self.release = Event()
        self.finished = Event()
        self.calls = 0
        self.verdict = verdict or {"correct": True, "message": "Correct!"}

    def __deepcopy__(self, memo: dict) -> "BlockingSphinx":
        return self

    def get_question(self) -> str:
        return "What repeats your words without a mouth?"

    def answer(self, text: str) -> dict:
        self.calls += 1
        self.started.set()
        self.release.wait(timeout=2)
        try:
            return self.verdict
        finally:
            self.finished.set()


class ProgrammableSphinx:
    """Double dont le résultat change à chaque appel successif."""
    def __init__(self, responses: list) -> None:
        self.responses = list(responses)

    def __deepcopy__(self, memo: dict) -> "ProgrammableSphinx":
        # Conserve la même instance pour que la liste responses soit bien dépilée à chaque appel
        return self

    def get_question(self) -> str:
        return "What repeats your words without a mouth?"

    def answer(self, text: str) -> dict:
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class TestSphinxEngine(unittest.TestCase):
    """Parties 1, 2 & 4 : règles du moteur, rencontre, suspension et verdicts."""
    def setUp(self) -> None:
        level = Level({
            "id": "test",
            "grid": ["#####", "#...#", "#####"],
            "start": {"x": 1, "y": 1},
            "exit": {"x": 2, "y": 1},
            "sphinx": True,
        })
        self.engine = Engine(level, Controller(TerminalInput()), BashRender())
        self.engine.sphinx = FakeSphinx()
        self.engine.apply_action("east")

    def test_public_state_hides_private_sphinx_data(self) -> None:
        state = self.engine.get_state()
        raw_text = repr(state)
        self.assertNotIn("expected_answer", raw_text)
        self.assertNotIn("history", raw_text)
        self.assertEqual(state["extras"], {})
        sphinx_entities = [e for e in state["entities"] if e["kind"] == "sphinx"]
        self.assertEqual(len(sphinx_entities), 1)
        self.assertEqual(set(sphinx_entities[0].keys()), {"id", "kind", "x", "y", "appearance"})

    def test_encounter_keeps_player_before_exit_and_suspends_moves(self) -> None:
        self.assertEqual(self.engine.player.get_position(), (1, 1))
        self.assertEqual(self.engine.status, "playing")
        self.assertEqual(self.engine.turn, 1)

        interaction = self.engine.get_state()["interaction"]
        self.assertEqual(interaction["status"], "question")
        self.assertEqual(interaction["question"], self.engine.sphinx.get_question())

        # Pendant le dialogue, east et wait sont ignorés sans consommer de tour
        self.engine.apply_action("east")
        self.engine.apply_action("wait")
        self.assertEqual(self.engine.player.get_position(), (1, 1))
        self.assertEqual(self.engine.turn, 1)

    def test_rejection_shows_hint_and_keeps_passage_closed(self) -> None:
        turn = self.engine.turn
        self.engine.apply_sphinx_verdict({"correct": False, "message": "Think about sound."})

        self.assertEqual(self.engine.player.get_position(), (1, 1))
        self.assertEqual(self.engine.status, "playing")
        self.assertEqual(self.engine.turn, turn)

        interaction = self.engine.get_state()["interaction"]
        self.assertIsNotNone(interaction)
        self.assertEqual(interaction["status"], "rejected")
        self.assertEqual(interaction["message"], "Think about sound.")

    def test_acceptance_wins_without_extra_turn(self) -> None:
        turn = self.engine.turn
        self.engine.apply_sphinx_verdict({"correct": True, "message": "Correct!"})

        self.assertEqual(self.engine.player.get_position(), (2, 1))
        self.assertEqual(self.engine.status, "won")
        self.assertEqual(self.engine.message, "Victory!")
        self.assertEqual(self.engine.turn, turn)
        self.assertIsNone(self.engine.get_state()["interaction"])


class TestSphinxHttpFlow(unittest.TestCase):
    """Parties 3, 4 & 5 : HTTP 202, pending, retries, erreurs, cancel et quit."""
    def _make_client(self, sphinx):
        level = Level({
            "id": "test",
            "grid": ["######", "#....#", "######"],
            "start": {"x": 1, "y": 1},
            "exit": {"x": 3, "y": 1},
            "sphinx": True,
        })
        engine = Engine(level, Controller(TerminalInput()), BashRender())
        engine.sphinx = sphinx
        client = create_app(engine).test_client()
        return engine, client

    def _trigger_encounter(self, client) -> dict:
        client.post("/api/actions", json={"action": "east"})
        res = client.post("/api/actions", json={"action": "east"})
        return res.get_json()["state"]["interaction"]

    def _wait_until_not_pending(self, client, timeout: float = 1.0) -> dict:
        deadline = time.time() + timeout
        while time.time() < deadline:
            frame = client.get("/api/state").get_json()
            interaction = frame["state"]["interaction"]
            if interaction is None or interaction["status"] != "pending":
                return frame
            time.sleep(0.01)
        self.fail("L'évaluation est restée bloquée sur pending")

    def test_answer_returns_202_pending_and_blocks_duplicate(self) -> None:
        blocking = BlockingSphinx()
        _, client = self._make_client(blocking)
        try:
            interaction = self._trigger_encounter(client)

            ans_res = client.post(
                "/api/answer",
                json={"interaction_id": interaction["id"], "answer": "  It is an echo.  "},
            )
            self.assertEqual(ans_res.status_code, 202)
            frame = ans_res.get_json()
            self.assertEqual(frame["state"]["interaction"]["status"], "pending")
            self.assertEqual(frame["state"]["turn"], 2)
            self.assertEqual(frame["revision"], 3)

            self.assertTrue(blocking.started.wait(timeout=1))

            # GET reste disponible pendant l'évaluation
            get_res = client.get("/api/state")
            self.assertEqual(get_res.status_code, 200)
            self.assertEqual(get_res.get_json()["state"]["interaction"]["status"], "pending")

            # Deuxième soumission pendant pending -> 409 evaluation_pending
            dup_res = client.post(
                "/api/answer",
                json={"interaction_id": interaction["id"], "answer": "Another try"},
            )
            self.assertEqual(dup_res.status_code, 409)
            self.assertEqual(dup_res.get_json()["error"]["code"], "evaluation_pending")
            self.assertEqual(blocking.calls, 1)
        finally:
            blocking.release.set()
            blocking.finished.wait(timeout=1)

    def test_rejected_error_and_retry_keep_same_question(self) -> None:
        sphinx = ProgrammableSphinx([
            {"correct": False, "message": "Think about sound."},
            RuntimeError("timeout / service unavailable"),
            {"correct": "false", "message": "Invalid non-boolean"},
            {"correct": True, "message": "Correct!"},
        ])
        _, client = self._make_client(sphinx)
        interaction = self._trigger_encounter(client)
        iid = interaction["id"]
        question = interaction["question"]

        # 1. Refus -> status="rejected", revision=4, turn=2
        client.post("/api/answer", json={"interaction_id": iid, "answer": "wind"})
        frame = self._wait_until_not_pending(client)
        self.assertEqual(frame["revision"], 4)
        self.assertEqual(frame["state"]["turn"], 2)
        self.assertEqual(frame["state"]["interaction"]["status"], "rejected")
        self.assertEqual(frame["state"]["interaction"]["question"], question)

        # 2. Panne technique -> status="error"
        client.post("/api/answer", json={"interaction_id": iid, "answer": "shadow"})
        frame = self._wait_until_not_pending(client)
        self.assertEqual(frame["state"]["interaction"]["status"], "error")
        self.assertEqual(
            frame["state"]["interaction"]["message"],
            "The evaluator is unavailable. Try again.",
        )

        # 3. Verdict invalide ("false" au lieu de booléen) -> status="error"
        client.post("/api/answer", json={"interaction_id": iid, "answer": "water"})
        frame = self._wait_until_not_pending(client)
        self.assertEqual(frame["state"]["interaction"]["status"], "error")

        # 4. Nouvelle tentative acceptée -> victoire
        client.post("/api/answer", json={"interaction_id": iid, "answer": "echo"})
        frame = self._wait_until_not_pending(client)
        self.assertEqual(frame["state"]["status"], "won")
        self.assertIsNone(frame["state"]["interaction"])

    def test_cancel_invalidates_stale_verdict_and_allows_new_encounter(self) -> None:
        blocking = BlockingSphinx(verdict={"correct": True, "message": "Correct!"})
        _, client = self._make_client(blocking)
        try:
            first_interaction = self._trigger_encounter(client)

            # Lance une évaluation qui reste bloquée
            client.post(
                "/api/answer",
                json={"interaction_id": first_interaction["id"], "answer": "echo"},
            )
            self.assertTrue(blocking.started.wait(timeout=1))

            # Annule le dialogue pendant que le modèle réfléchit -> 200 et interaction=None
            cancel_res = client.post(
                "/api/cancel",
                json={"interaction_id": first_interaction["id"]},
            )
            self.assertEqual(cancel_res.status_code, 200)
            cancel_frame = cancel_res.get_json()
            self.assertIsNone(cancel_frame["state"]["interaction"])
            self.assertEqual(cancel_frame["state"]["status"], "playing")

            # Démarre une nouvelle rencontre -> nouvel id, même énigme
            re_res = client.post("/api/actions", json={"action": "east"})
            second_interaction = re_res.get_json()["state"]["interaction"]
            self.assertNotEqual(second_interaction["id"], first_interaction["id"])
            self.assertEqual(second_interaction["question"], first_interaction["question"])
            self.assertEqual(second_interaction["status"], "question")

            before_stale_return = client.get("/api/state").get_json()

            # Libère l'ancien jugement périmé et attend sa fin
            blocking.release.set()
            self.assertTrue(blocking.finished.wait(timeout=1))
            time.sleep(0.02)

            # L'état doit être strictement identique (pas de victoire ni d'écrasement)
            after_stale_return = client.get("/api/state").get_json()
            self.assertEqual(after_stale_return, before_stale_return)
        finally:
            blocking.release.set()

    def test_quit_during_pending_ignores_stale_verdict(self) -> None:
        blocking = BlockingSphinx(verdict={"correct": True, "message": "Correct!"})
        _, client = self._make_client(blocking)
        try:
            interaction = self._trigger_encounter(client)

            client.post(
                "/api/answer",
                json={"interaction_id": interaction["id"], "answer": "echo"},
            )
            self.assertTrue(blocking.started.wait(timeout=1))

            # Quitter pendant l'attente
            quit_res = client.post("/api/actions", json={"action": "quit"})
            self.assertEqual(quit_res.status_code, 200)
            quit_frame = quit_res.get_json()
            self.assertFalse(quit_frame["running"])
            self.assertEqual(quit_frame["state"]["status"], "lost")
            self.assertIsNone(quit_frame["state"]["interaction"])

            # Libère le jugement périmé
            blocking.release.set()
            self.assertTrue(blocking.finished.wait(timeout=1))
            time.sleep(0.02)

            # GET reste disponible avec running=false et passage toujours fermé
            final_frame = client.get("/api/state").get_json()
            self.assertFalse(final_frame["running"])
            self.assertEqual(final_frame["state"]["status"], "lost")
            self.assertEqual(final_frame, quit_frame)
        finally:
            blocking.release.set()

    def test_request_validation_errors_do_not_mutate_state(self) -> None:
        _, client = self._make_client(FakeSphinx())
        interaction = self._trigger_encounter(client)
        before = client.get("/api/state").get_json()

        # Mauvais Content-Type -> 415
        res_415 = client.post("/api/answer", data="not json")
        self.assertEqual(res_415.status_code, 415)

        # Champs manquants/inconnus -> 422
        res_422_fields = client.post("/api/answer", json={"interaction_id": interaction["id"]})
        self.assertEqual(res_422_fields.status_code, 422)

        # Réponse vide après trim ou > 500 caractères -> 422
        res_empty = client.post("/api/answer", json={"interaction_id": interaction["id"], "answer": "   "})
        self.assertEqual(res_empty.status_code, 422)
        res_long = client.post("/api/answer", json={"interaction_id": interaction["id"], "answer": "x" * 501})
        self.assertEqual(res_long.status_code, 422)

        # Mauvais interaction_id -> 409 stale_interaction
        res_stale = client.post("/api/answer", json={"interaction_id": "wrong-id", "answer": "echo"})
        self.assertEqual(res_stale.status_code, 409)
        self.assertEqual(res_stale.get_json()["error"]["code"], "stale_interaction")

        # Aucune mutation n'a eu lieu
        after = client.get("/api/state").get_json()
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()