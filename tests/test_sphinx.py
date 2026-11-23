"""Use the supplied fake; these tests must never contact Ollama."""
from gridworld.llm_support import fake_llm_json
from gridworld.sphinx import Sphinx


def test_question_is_generated_once():
    calls = []
    def ask(prompt, data, kind):
        calls.append(kind)
        return fake_llm_json(prompt, data, kind)
    sphinx = Sphinx(ask=ask)
    question = sphinx.get_question()
    assert isinstance(question, str) and question
    assert sphinx.get_question() == question
    assert calls == ["riddle"]


def test_wrong_answers_keep_history():
    sphinx = Sphinx(ask=fake_llm_json)
    question = sphinx.get_question()

    first = sphinx.answer("a clock")
    second = sphinx.answer("a stone")

    assert first["correct"] is False
    assert second["correct"] is False
    assert sphinx.history == [
        {"answer": "a clock", "hint": first["message"]},
        {"answer": "a stone", "hint": second["message"]},
    ]
    assert sphinx.get_question() == question


def test_correct_answer_clears_history():
    sphinx = Sphinx(ask=fake_llm_json)
    sphinx.answer("a clock")
    assert len(sphinx.history) == 1

    result = sphinx.answer("an echo")

    assert result == {"correct": True, "message": "Correct!"}
    assert sphinx.history == []
