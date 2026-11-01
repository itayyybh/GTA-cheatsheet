"""Week 6 tests for the web app (app.py at the project root).

Needs:  pip install fastapi uvicorn httpx
Run:    pytest tests/test_week6_app.py

app.py must define `create_app(answer_fn, log_path)` that returns a FastAPI app.
`answer_fn(question)` returns a result dict like answer_question's
({"answer", "sources", "refused"}) and may add a "game" key.
The tests pass a fake answer_fn, so nothing calls Claude or loads a model.
If fastapi isn't installed, this whole file is skipped (not failed).
"""

import json

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient   # noqa: E402

import cheatsheet as cs   # noqa: E402

STICKY = {"n": 1, "title": "Sticky Bombs", "section": "Grand Theft Auto V",
          "url": "https://gta.wiki/wiki/Sticky_Bombs"}


class FakeAnswer:
    def __init__(self, reply=None, error=None):
        self.reply = reply or {"answer": "$400 each [1].", "sources": [STICKY], "refused": False, "game": "V"}
        self.error = error
        self.questions = []

    def __call__(self, question):
        self.questions.append(question)
        if self.error:
            raise self.error
        return self.reply


@pytest.fixture
def make_client(tmp_path):
    import app as web     # imported here so a missing app.py only fails these tests

    def _make(answer_fn):
        log_path = tmp_path / "questions.jsonl"
        return TestClient(web.create_app(answer_fn, log_path)), log_path
    return _make


# ---------- Day 4: the page and /ask ----------

def test_week6_app_home_page_has_a_form(make_client):
    client, _ = make_client(FakeAnswer())
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "<form" in r.text.lower()


def test_week6_app_ask_returns_answer_and_links(make_client):
    fake = FakeAnswer()
    client, _ = make_client(fake)
    r = client.post("/ask", json={"question": "  sticky bombs price  "})
    assert r.status_code == 200
    assert r.json() == {
        "answer": "$400 each [1].",
        "refused": False,
        "game": "V",
        "sources": [{"title": "Sticky Bombs", "url": "https://gta.wiki/wiki/Sticky_Bombs"}],
    }
    assert fake.questions == ["sticky bombs price"]     # stripped before answering


def test_week6_app_ask_refusal(make_client):
    fake = FakeAnswer({"answer": "Not documented yet.", "sources": [], "refused": True})
    client, _ = make_client(fake)
    body = client.post("/ask", json={"question": "lester voice actor"}).json()
    assert body["refused"] is True
    assert body["sources"] == []
    assert body["game"] is None          # result had no "game" key


def test_week6_app_rejects_bad_questions_without_calling_the_model(make_client):
    fake = FakeAnswer()
    client, log_path = make_client(fake)
    r1 = client.post("/ask", json={"question": "   "})
    r2 = client.post("/ask", json={"question": "a" * 301})
    assert (r1.status_code, r1.json()) == (400, {"error": "empty"})
    assert (r2.status_code, r2.json()) == (400, {"error": "too_long"})
    assert fake.questions == []
    assert cs.read_jsonl(log_path) == []


# ---------- Day 5: logging, errors, /stats ----------

def test_week6_app_logs_every_answered_question(make_client):
    client, log_path = make_client(FakeAnswer())
    client.post("/ask", json={"question": "a"})
    client.post("/ask", json={"question": "b"})
    entries = cs.read_jsonl(log_path)
    assert [e["question"] for e in entries] == ["a", "b"]
    assert entries[0]["game"] == "V"
    assert entries[0]["sources"] == ["https://gta.wiki/wiki/Sticky_Bombs"]
    assert entries[0]["seconds"] >= 0
    assert entries[0]["error"] is None
    assert entries[0]["time"].startswith("20")      # an ISO timestamp


def test_week6_app_model_error_is_503_and_logged(make_client):
    client, log_path = make_client(FakeAnswer(error=TimeoutError("slow")))
    r = client.post("/ask", json={"question": "is the kuruma awd"})
    assert (r.status_code, r.json()) == (503, {"error": "model_unavailable"})
    entries = cs.read_jsonl(log_path)
    assert len(entries) == 1
    assert entries[0]["error"] == "TimeoutError"
    assert entries[0]["refused"] is True


def test_week6_app_stats(make_client):
    client, _ = make_client(FakeAnswer())
    client.post("/ask", json={"question": "a"})
    client.post("/ask", json={"question": "b"})
    s = client.get("/stats").json()
    assert s["count"] == 2
    assert s["refused"] == 0
    assert s["by_game"] == {"V": 2}
