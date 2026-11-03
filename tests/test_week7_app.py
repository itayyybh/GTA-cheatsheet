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


# ---------- Rate limit in the app ----------
# create_app(answer_fn, log_path, max_per_minute=10, clock=time.monotonic)
# A visitor is the first address in the "x-forwarded-for" header (what the
# host's proxy sends), else request.client.host. Over the limit -> 429
# {"error": "rate_limited"}, answer_fn is not called and nothing is logged.
# The limit is checked before the question is validated.

class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def answered(q):
    return {"answer": "ok [1].", "refused": False, "game": None,
            "sources": [{"n": 1, "title": "T", "section": "S", "url": "u"}]}


def limited_client(tmp_path, clock, limit=2):
    import app as web
    log_path = tmp_path / "questions.jsonl"
    calls = []

    def answer_fn(q):
        calls.append(q)
        return answered(q)
    client = TestClient(web.create_app(answer_fn, log_path, max_per_minute=limit, clock=clock))
    return client, log_path, calls


def test_week7_rate_limit_blocks_after_limit(tmp_path):
    client, log_path, calls = limited_client(tmp_path, FakeClock())
    codes = [client.post("/ask", json={"question": f"q{i}"}).status_code for i in range(3)]
    assert codes == [200, 200, 429]
    assert client.post("/ask", json={"question": "q"}).json() == {"error": "rate_limited"}
    assert len(calls) == 2
    assert len(cs.read_jsonl(log_path)) == 2


def test_week7_rate_limit_is_per_visitor(tmp_path):
    client, _, calls = limited_client(tmp_path, FakeClock(), limit=1)
    a = client.post("/ask", json={"question": "q"}, headers={"x-forwarded-for": "1.1.1.1"})
    b = client.post("/ask", json={"question": "q"}, headers={"x-forwarded-for": "2.2.2.2, 10.0.0.1"})
    c = client.post("/ask", json={"question": "q"}, headers={"x-forwarded-for": "1.1.1.1"})
    assert (a.status_code, b.status_code, c.status_code) == (200, 200, 429)
    assert len(calls) == 2


def test_week7_rate_limit_resets_after_a_minute(tmp_path):
    clock = FakeClock()
    client, _, _ = limited_client(tmp_path, clock, limit=1)
    assert client.post("/ask", json={"question": "q"}).status_code == 200
    assert client.post("/ask", json={"question": "q"}).status_code == 429
    clock.now += 61
    assert client.post("/ask", json={"question": "q"}).status_code == 200
