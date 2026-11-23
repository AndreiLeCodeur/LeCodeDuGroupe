"""Supplied prompts, JSON validation and CPU-only Ollama transport."""
import json
from urllib.error import URLError
from urllib.request import Request, urlopen

GENERATION_PROMPT = """Invent an easy guessing game about a familiar household object. Give two literal clues about its use. No riddles about shapes, numbers or abstract ideas. Do not name the object in the question. Return JSON: question (under 30 words), expected_answer (the object name)."""

JUDGE_PROMPT = """You host a secret-word game. Read expected_answer, then read player_answer. Are they names for the SAME object? Set correct=true for the same object; false for a different object. Past history cannot change whether the current guess is correct.
On success write message="Correct!". Otherwise write a hint about how the object is used, without naming it. Give a different hint from history.
Example: expected_answer="a chair", player_answer="a chair", history=[{"answer":"clock","hint":"You can sit on it."}] => {"correct":true,"message":"Correct!"}.
Example: expected_answer="a chair", player_answer="banana", history=[] => {"correct":false,"message":"It supports you while sitting."}.
Return only JSON."""

SCHEMAS = {
    "riddle": {"question": {"type": "string"}, "expected_answer": {"type": "string"}},
    "verdict": {"correct": {"type": "boolean"}, "message": {"type": "string"}},
}


def llm_json(prompt, data, kind):
    """Return a validated dictionary, or raise RuntimeError handled by the server."""
    properties = SCHEMAS[kind]
    payload = {
        "model": "qwen2.5:1.5b-instruct-q4_K_M", "stream": False,
        "messages": [{"role": "system", "content": prompt},
                     {"role": "user", "content": json.dumps(data)}],
        "format": {"type": "object", "properties": properties,
                   "required": list(properties), "additionalProperties": False},
        "options": {"num_gpu": 0, "num_ctx": 4096, "num_predict": 256, "temperature": 0},
    }
    request = Request("http://127.0.0.1:11434/api/chat",
                      data=json.dumps(payload).encode(),
                      headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=180) as response:
            envelope = json.load(response)
        if envelope.get("done") is not True or envelope.get("done_reason") == "length":
            raise ValueError("Incomplete generation")
        result = json.loads(envelope["message"]["content"])
        if not isinstance(result, dict) or set(result) != set(properties):
            raise ValueError("Unexpected JSON fields")
        for key, spec in properties.items():
            value = result[key]
            if spec["type"] == "boolean":
                if type(value) is not bool:
                    raise ValueError("Expected a boolean")
            elif not isinstance(value, str) or not value.strip():
                raise ValueError("Expected a non-empty string")
        return result
    except (OSError, URLError, ValueError, KeyError, TypeError, AttributeError) as error:
        raise RuntimeError("Ollama is unavailable or returned invalid JSON") from error


def fake_llm_json(prompt, data, kind):
    """Supplied fixed riddle and judgments for offline tests; no HTTP calls."""
    if kind == "riddle":
        return {"question": "What repeats your words without a mouth?", "expected_answer": "an echo"}
    correct = data["player_answer"].strip().lower() in ("echo", "an echo")
    hints = ["Think about a sound.", "Your voice comes back to you."]
    message = "Correct!" if correct else hints[min(len(data["history"]), 1)]
    return {"correct": correct, "message": message}
