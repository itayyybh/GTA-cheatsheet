"""Week 7 tests: the gate score in the log.

The refusal gate's score is computed for every question but was thrown away.
Logging it tells gate refusals (score below the threshold) apart from Claude
refusals (score fine, no answer in the chunks).

How the score travels:
  runs/serve.py   answer_with_game computes score = gate_score(question) once,
                  passes `lambda q: score` to answer_question as score_fn,
                  and returns {**result, "game": game, "score": score}
  app.py          after building the entry with log_entry, adds
                  entry["score"] = the result's "score" rounded to 3 decimals,
                  or None when the result has no "score" (or answer_fn failed)

log_entry and answer_question don't change, so the Week 4 and Week 6 tests
still pass. The /ask response doesn't change either: the score is only logged.

Needs fastapi installed (skipped otherwise). Run: pytest tests/test_week7_app.py
"""

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient   # noqa: E402

import cheatsheet as cs   # noqa: E402


def make_client(tmp_path, answer_fn):
    import app as web
    log_path = tmp_path / "questions.jsonl"
    return TestClient(web.create_app(answer_fn, log_path)), log_path


def test_week7_score_is_logged_rounded(tmp_path):
    reply = {"answer": "Not documented yet.", "sources": [], "refused": True,
             "game": None, "score": 0.51234}
    client, log_path = make_client(tmp_path, lambda q: reply)
    client.post("/ask", json={"question": "trevers special abilty"})
    assert cs.read_jsonl(log_path)[0]["score"] == 0.512


def test_week7_score_is_not_in_the_response(tmp_path):
    reply = {"answer": "Area Kill [1].", "refused": False, "game": None, "score": 0.7,
             "sources": [{"n": 1, "title": "Michael De Santa", "section": "Skills", "url": "u"}]}
    client, _ = make_client(tmp_path, lambda q: reply)
    body = client.post("/ask", json={"question": "michael special"}).json()
    assert "score" not in body


def test_week7_missing_score_is_none(tmp_path):
    reply = {"answer": "x [1].", "refused": False,
             "sources": [{"n": 1, "title": "T", "section": "S", "url": "u"}]}
    client, log_path = make_client(tmp_path, lambda q: reply)
    client.post("/ask", json={"question": "q"})
    assert cs.read_jsonl(log_path)[0]["score"] is None


def test_week7_model_error_logs_score_none(tmp_path):
    def broken(q):
        raise TimeoutError("slow")
    client, log_path = make_client(tmp_path, broken)
    client.post("/ask", json={"question": "q"})
    assert cs.read_jsonl(log_path)[0]["score"] is None
