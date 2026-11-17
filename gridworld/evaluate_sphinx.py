"""Manual CPU evaluation entry point; never invoked by pytest."""

import argparse
import json
import os
from pathlib import Path
import platform
from time import perf_counter
from typing import Any

from gridworld.sphinx_service import (
    CPU_OPTIONS,
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT,
    DEFAULT_URL,
    OllamaSphinxService,
    Riddle,
    ServiceError,
    SphinxService,
)

# Cases handled elsewhere (S2-04): HTTP validation, simulated failures, cancellation.
SIMULATED_KEYS = ("expected_http", "service_failure", "service_reply", "cancel_before_verdict")
BINARY_OUTCOMES = ("correct", "false_positive", "false_negative")


def build_answer(case: dict[str, Any]) -> str:
    """Return the text the API would give to the judge (trimmed)."""
    if "answer" in case:
        text = case["answer"]
    else:
        recipe = case["answer_recipe"]
        pad = " " * recipe.get("surround_with_spaces", 0)
        text = pad + recipe["repeat"] * recipe["count"] + pad
    return text.strip()


def evaluate_cases(
    service: SphinxService, riddle: Riddle, cases: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Evaluate labelled answers and record failures and timings separately."""
    reference_words = [w for w in riddle.expected_answer.lower().split() if len(w) > 2]
    results = []
    for case in cases:
        if any(key in case for key in SIMULATED_KEYS):
            continue
        ambiguous = case.get("ambiguous") is True
        expected = case.get("expected")
        if not ambiguous and expected not in ("accepted", "rejected"):
            continue

        answer = build_answer(case)
        record: dict[str, Any] = {
            "id": case["id"],
            "family": case.get("family"),
            "answer": answer if len(answer) <= 80 else answer[:77] + "...",
            "answer_length": len(answer),
            "expected": None if ambiguous else expected,
        }

        start = perf_counter()
        try:
            verdict = service.judge(riddle, answer)
            record["verdict"] = {"accepted": verdict.accepted, "message": verdict.message}
            record["error"] = None
            record["message_mentions_reference"] = any(
                word in verdict.message.lower() for word in reference_words
            )
        except ServiceError as exc:
            record["verdict"] = None
            record["error"] = type(exc).__name__
        record["elapsed_seconds"] = round(perf_counter() - start, 3)

        if record["error"] is not None:
            record["outcome"] = "service_error"      # never counted as a refusal
        elif ambiguous:
            record["outcome"] = "ambiguous"          # outside the binary score
        else:
            got = "accepted" if record["verdict"]["accepted"] else "rejected"
            if got == expected:
                record["outcome"] = "correct"
            elif got == "accepted":
                record["outcome"] = "false_positive"  # wrong answer accepted
            else:
                record["outcome"] = "false_negative"  # right answer refused
        results.append(record)
    return results


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for record in results:
        counts[record["outcome"]] = counts.get(record["outcome"], 0) + 1
    scored = sum(counts.get(name, 0) for name in BINARY_OUTCOMES)
    times = [r["elapsed_seconds"] for r in results]
    return {
        "counts": counts,
        "binary_score": f"{counts.get('correct', 0)}/{scored}",
        "first_call_seconds": times[0] if times else None,
        "other_calls_mean_seconds": round(sum(times[1:]) / len(times[1:]), 3)
        if len(times) > 1
        else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate a local sphinx model")
    parser.add_argument("--riddle", required=True, help="S2-02 map JSON")
    parser.add_argument("--corpus", required=True, help="S2-02 evaluation corpus")
    parser.add_argument("--output", required=True, help="Local JSON report")
    parser.add_argument("--url", default=DEFAULT_URL, help="Ollama base URL, without /api")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--cpu-note", required=True, help="CPU/RAM and observed CPU execution")
    parser.add_argument("--notes", default="", help="Short interpretation of the results")
    args = parser.parse_args()

    map_data = json.loads(Path(args.riddle).read_text(encoding="utf-8"))
    corpus = json.loads(Path(args.corpus).read_text(encoding="utf-8"))

    sphinx = map_data.get("sphinx")
    if isinstance(sphinx, dict) and "riddle" in sphinx:
        riddle = Riddle(**sphinx["riddle"])
    else:
        # The S2-02 map only flags the sphinx; the fixed riddle lives in the corpus.
        data = corpus["riddle"]
        riddle = Riddle(corpus["riddle_id"], data["question"], data["expected_answer"])

    service = OllamaSphinxService(args.url, args.model, args.timeout)
    results = evaluate_cases(service, riddle, corpus["cases"])
    report = {
        "model": args.model,
        "url": args.url,
        "timeout_seconds": args.timeout,
        "options": CPU_OPTIONS,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "python": platform.python_version(),
        "cpu_note": args.cpu_note,
        "riddle_id": riddle.id,
        "summary": summarize(results),
        "results": results,
        "interpretation": args.notes,
    }
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()