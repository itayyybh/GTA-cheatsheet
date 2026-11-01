"""Week 6 tests for the GTA cheatsheet: logging and the web layer's helpers.

Your code goes in cheatsheet.py. Run from the project root:
    pytest tests/test_week6.py              all Week 6 helper tests
    pytest -k log_entry                     one exercise

Nothing here calls Claude or loads a model. Time is passed in as a string
(`when`) so the tests never depend on the real clock.

The tests call functions as `cs.name(...)`, so a function you haven't written
yet only fails its own tests. No placeholders needed.
"""

import json

import cheatsheet as cs


def result(answer="It costs $400 [1].", refused=False, sources=None):
    if sources is None:
        sources = [{"n": 1, "title": "Sticky Bombs", "section": "Grand Theft Auto V",
                    "url": "https://gta.wiki/wiki/Sticky_Bombs"}]
    return {"answer": answer, "sources": sources, "refused": refused}


REFUSED = {"answer": "Not documented yet.", "sources": [], "refused": True}
WHEN = "2026-11-02T18:30:00+00:00"


# ---------- Day 1: log_entry / append_jsonl / read_jsonl ----------

def test_week6_log_entry_fields():
    e = cs.log_entry("sticky bombs price", result(), "V", 1.23456, WHEN)
    assert e == {
        "time": WHEN,
        "question": "sticky bombs price",
        "game": "V",
        "refused": False,
        "answer": "It costs $400 [1].",
        "sources": ["https://gta.wiki/wiki/Sticky_Bombs"],
        "seconds": 1.23,
        "error": None,
    }


def test_week6_log_entry_refused_and_no_game():
    e = cs.log_entry("lester voice actor", REFUSED, None, 0.1, WHEN)
    assert e["refused"] is True
    assert e["game"] is None
    assert e["sources"] == []


def test_week6_log_entry_error_is_kept():
    e = cs.log_entry("q", REFUSED, None, 0.5, WHEN, error="APITimeoutError")
    assert e["error"] == "APITimeoutError"


def test_week6_append_jsonl_one_line_per_entry(tmp_path):
    path = tmp_path / "logs" / "questions.jsonl"      # folder doesn't exist yet
    cs.append_jsonl(path, {"question": "a"})
    cs.append_jsonl(path, {"question": "b"})
    lines = path.read_text(encoding="utf-8").splitlines()
    assert [json.loads(l)["question"] for l in lines] == ["a", "b"]


def test_week6_append_jsonl_keeps_non_ascii_readable(tmp_path):
    path = tmp_path / "q.jsonl"
    cs.append_jsonl(path, {"question": "café"})
    assert "café" in path.read_text(encoding="utf-8")   # not "café"


def test_week6_read_jsonl_roundtrip_and_blank_lines(tmp_path):
    path = tmp_path / "q.jsonl"
    path.write_text('{"a": 1}\n\n{"a": 2}\n', encoding="utf-8")
    assert cs.read_jsonl(path) == [{"a": 1}, {"a": 2}]


def test_week6_read_jsonl_missing_file_is_empty(tmp_path):
    assert cs.read_jsonl(tmp_path / "nope.jsonl") == []


# ---------- Day 2: log_summary ----------

def test_week6_log_summary_counts():
    entries = [
        cs.log_entry("a", result(), "V", 1.0, WHEN),
        cs.log_entry("b", REFUSED, None, 2.0, WHEN),
        cs.log_entry("c", result(), "V", 3.0, WHEN),
        cs.log_entry("d", REFUSED, "Online", 4.0, WHEN, error="Boom"),
    ]
    s = cs.log_summary(entries)
    assert s == {
        "count": 4,
        "refused": 2,
        "refusal_rate": 0.5,
        "errors": 1,
        "avg_seconds": 2.5,
        "by_game": {"V": 2, "none": 1, "Online": 1},
    }


def test_week6_log_summary_rounding():
    entries = [cs.log_entry(q, REFUSED if q == "a" else result(), None, sec, WHEN)
               for q, sec in [("a", 1.0), ("b", 1.0), ("c", 2.0)]]
    s = cs.log_summary(entries)
    assert s["refusal_rate"] == 0.333        # 1/3 rounded to 3 decimals
    assert s["avg_seconds"] == 1.33          # 4/3 rounded to 2 decimals


def test_week6_log_summary_empty():
    assert cs.log_summary([]) == {"count": 0, "refused": 0, "refusal_rate": 0.0,
                                  "errors": 0, "avg_seconds": 0.0, "by_game": {}}


# ---------- Day 3: validate_question / source_links ----------

def test_week6_validate_question_strips():
    assert cs.validate_question("  is the kuruma awd  ") == ("is the kuruma awd", None)


def test_week6_validate_question_empty():
    assert cs.validate_question("   ") == (None, "empty")
    assert cs.validate_question("") == (None, "empty")


def test_week6_validate_question_too_long():
    assert cs.validate_question("a" * 301) == (None, "too_long")
    assert cs.validate_question("a" * 300) == ("a" * 300, None)
    assert cs.validate_question("abcdef", max_chars=5) == (None, "too_long")


def test_week6_source_links_one_per_page_in_order():
    sources = [
        {"n": 2, "title": "Buzzard Attack Chopper", "section": "Weaponry", "url": "https://gta.wiki/wiki/Buzzard"},
        {"n": 1, "title": "Sticky Bombs", "section": "Infobox", "url": "https://gta.wiki/wiki/Sticky_Bombs"},
        {"n": 4, "title": "Buzzard Attack Chopper", "section": "Design", "url": "https://gta.wiki/wiki/Buzzard"},
    ]
    assert cs.source_links(sources) == [
        {"title": "Buzzard Attack Chopper", "url": "https://gta.wiki/wiki/Buzzard"},
        {"title": "Sticky Bombs", "url": "https://gta.wiki/wiki/Sticky_Bombs"},
    ]


def test_week6_source_links_empty():
    assert cs.source_links([]) == []
