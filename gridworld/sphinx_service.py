"""S2-03 starter: complete the service methods marked TODO."""

from dataclasses import dataclass, field
from http.client import HTTPException
import json
from math import isfinite
from typing import Any, Protocol
from urllib.error import URLError
from urllib.request import Request, urlopen
from uuid import uuid4


DEFAULT_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5:1.5b-instruct-q4_K_M"
DEFAULT_TIMEOUT = 180.0
CPU_OPTIONS = {
    "num_gpu": 0,
    "num_ctx": 2048,
    "num_predict": 128,
    "temperature": 0,
    "seed": 0,
}


@dataclass(frozen=True)
class Riddle:
    id: str
    question: str
    expected_answer: str = field(repr=False)


@dataclass(frozen=True)
class Verdict:
    accepted: bool
    message: str


class SphinxService(Protocol):
    def create_riddle(self, theme: str) -> Riddle: ...
    def judge(self, riddle: Riddle, answer: str) -> Verdict: ...


class ServiceError(Exception):
    """A technical failure, not a rejected player answer."""


class ServiceTimeout(ServiceError):
    """The evaluation exceeded the configured timeout."""


class ServiceUnavailable(ServiceError):
    """The service could not complete the HTTP exchange."""


class InvalidServiceResponse(ServiceError):
    """The response did not match the agreed data contract."""


def require_text(data: dict[str, Any], name: str) -> str:
    """Return a non-blank string or raise InvalidServiceResponse."""
    # TODO: validate the value, without coercing another type into a string.
    raise NotImplementedError("TODO: validate a text field")


class OllamaSphinxService:
    def __init__(
        self,
        url: str = DEFAULT_URL,
        model: str = DEFAULT_MODEL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        # Configuration is provided; no request happens during construction.
        if not isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        self.url = url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _chat(
        self,
        instruction: str,
        data: dict[str, Any],
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        """Send one CPU request and validate the JSON envelope and fields."""
        # TODO: build a strict object schema from properties (all required).
        # TODO: POST /api/chat with stream=False, CPU_OPTIONS and a finite timeout.
        # Keep instruction in a system message and JSON-encoded data in a user message.
        # TODO: map transport failures to ServiceTimeout or ServiceUnavailable.
        # TODO: require done=True; decode message.content as a JSON object.
        # Reject missing/extra fields and malformed replies with InvalidServiceResponse.
        raise NotImplementedError("TODO: implement the Ollama exchange")

    def create_riddle(self, theme: str) -> Riddle:
        """Generate one question and keep its reference answer on the server."""
        # TODO: call _chat, validate both strings and assign a non-empty id.
        # Expected fields: question and expected_answer.
        raise NotImplementedError("TODO: create and validate a riddle")

    def judge(self, riddle: Riddle, answer: str) -> Verdict:
        """Evaluate untrusted answer text; return a validated verdict."""
        # TODO: send the question, reference answer and player text as data.
        # Expected fields: accepted (a real bool) and message (non-blank str).
        # A technical failure must raise ServiceError, not return accepted=False.
        raise NotImplementedError("TODO: evaluate and validate an answer")


class FakeSphinxService:
    """Select an outcome for repeatable tests, without making any request."""

    def __init__(self, outcome: str = "accepted"):
        if outcome not in ("accepted", "rejected", "timeout", "unavailable", "invalid"):
            raise ValueError("Unknown fake outcome")
        self.outcome = outcome

    def create_riddle(self, theme: str) -> Riddle:
        return Riddle(
        id="echo",
        question="What repeats your words without having a voice of its own?",
        expected_answer="an echo",
    )

    def judge(self, riddle: Riddle, answer: str) -> Verdict:
        if self.outcome == "accepted":
            return Verdict(True, "Correct.")
        if self.outcome == "rejected":
            return Verdict(False, "Not quite, try again.")
        if self.outcome == "timeout":
            raise ServiceTimeout("Simulated timeout")
        if self.outcome == "unavailable":
            raise ServiceUnavailable("Simulated unavailable service")
        raise InvalidServiceResponse("Simulated invalid response")