"""Complete the two public methods; transport and prompts are supplied."""
from gridworld.llm_support import llm_json


class Sphinx:
    def __init__(self, ask=llm_json):
        self.ask = ask
        self.riddle = None
        self.history = []

    def get_question(self) -> str:
        """Generate and cache one riddle; return only its public question."""
        # TODO: if riddle is None, use ask(GENERATION_PROMPT, {}, "riddle").
        # Keep the validated dictionary, including its private expected_answer.
        # Return the cached question on every call.
        raise NotImplementedError("Complete Sphinx.get_question")

    def answer(self, player_text: str) -> dict:
        """Judge an answer, remember a failed attempt, or clear history on success."""
        # TODO: ensure a riddle exists by calling get_question().
        # Build data with question, expected_answer, player_answer and history.
        # Use ask(JUDGE_PROMPT, data, "verdict").
        # If correct: force message to "Correct!" and clear history.
        # Otherwise append {"answer": player_text, "hint": result["message"]}.
        # Return the verdict. Never modify the engine here.
        raise NotImplementedError("Complete Sphinx.answer")
