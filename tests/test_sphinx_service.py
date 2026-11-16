"""S2-03 offline tests: one complete example and seven tests to write."""

from http.client import IncompleteRead
from io import BytesIO
import json
from urllib.error import URLError

import pytest

from gridworld import sphinx_service as service


@pytest.fixture(autouse=True)
def no_real_network(monkeypatch):
    """Prevent an accidental real request through the starter's transport."""
    def blocked(*args, **kwargs):
        pytest.fail("A test tried to contact the real LLM; replace urlopen first")

    monkeypatch.setattr(service, "urlopen", blocked)


@pytest.fixture
def riddle():
    return service.Riddle(
        "echo",
        "What repeats your words without having a voice of its own?",
        "an echo",
    )


def reply(data):
    """Build an in-memory Ollama response; no server is started."""
    envelope = {"done": True, "message": {"content": json.dumps(data)}}
    return BytesIO(json.dumps(envelope).encode("utf-8"))


@pytest.mark.parametrize("accepted", ["false", 0, 1, None])
def test_judge_rejects_non_boolean(monkeypatch, riddle, accepted):
    """Complete example: JSON values must not be converted with bool(...)."""
    monkeypatch.setattr(
        service,
        "urlopen",
        lambda *args, **kwargs: reply({"accepted": accepted, "message": "Try again"}),
    )
    with pytest.raises(service.InvalidServiceResponse):
        service.OllamaSphinxService().judge(riddle, "an echo")


def test_fake_verdicts_are_repeatable(riddle):
    for outcome, expected in [("accepted", True), ("rejected", False)]:
        fake = service.FakeSphinxService(outcome)
        first = fake.judge(riddle, "an echo")
        second = fake.judge(riddle, "an echo")
        assert first == second          # même résultat à chaque appel
        assert first.accepted is expected


def test_fake_failures(riddle):
    expected_errors = {
        "timeout": service.ServiceTimeout,
        "unavailable": service.ServiceUnavailable,
        "invalid": service.InvalidServiceResponse,
    }
    for outcome, error in expected_errors.items():
        with pytest.raises(error):
            service.FakeSphinxService(outcome).judge(riddle, "an echo")


def test_request_configuration_and_answer_separation(monkeypatch, riddle):
    """Capture request/timeout; check CPU, schema, URL/model and message roles."""
    # Return a reply with accepted=False: a valid rejection is not an exception.
    # Use an instruction-like answer and check it stays in the user JSON data.
    pytest.fail("TODO: inspect a substituted HTTP request and a valid verdict")


def test_invalid_envelopes_and_fields(monkeypatch, riddle):
    """Cover broken JSON, done=False, missing/extra fields and bad text types."""
    # BytesIO(b"{") can simulate malformed JSON; reply(...) builds a valid envelope.
    pytest.fail("TODO: reject malformed replies and schema violations")


def test_transport_failures(monkeypatch, riddle):
    """Replace urlopen with a callable that raises a transport exception."""
    # Cover TimeoutError, URLError(TimeoutError()), URLError("connection refused"),
    # ConnectionResetError and IncompleteRead(b"{"). Check the mapped exception.
    pytest.fail("TODO: distinguish timeout from unavailability")


def test_timeout_is_finite_and_positive():
    """Try zero, a negative number, infinity and NaN; expect ValueError."""
    pytest.fail("TODO: check invalid timeout configuration")


def test_create_riddle_and_private_reference(monkeypatch):
    """Substitute replies; check id/text, invalid fields and the fixed fake riddle."""
    # Check the reference is absent from repr(riddle), but available server-side.
    # repr=False does not make dataclasses.asdict safe for public game state.
    pytest.fail("TODO: check generated and deterministic riddles")