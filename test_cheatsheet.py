"""Week 1 tests for the GTA cheatsheet.

Your code goes in cheatsheet.py, in the same folder.
Run everything:        pytest
Run one exercise:      pytest -k clean_text
"""

from cheatsheet import (
    clean_text,
    split_sections,
    make_chunks,
    save_chunks,
    load_chunks,
    parse_api_response,
    keyword_search,
    recall_at_k,
)

SAMPLE_TEXT = (
    "The Kuruma is a car.\n"
    "== Location ==\n"
    "Found in Rockford Hills.\n"
    "== Price ==\n"
    "$95,000"
)

SAMPLE_PAGE = {
    "title": "Kuruma",
    "url": "https://example.wiki/wiki/Kuruma",
    "text": SAMPLE_TEXT,
}

CHUNKS = [
    {"title": "Kuruma", "section": "Location", "url": "u1",
     "text": "Found in Rockford Hills garage"},
    {"title": "Kuruma", "section": "Price", "url": "u2",
     "text": "Costs 95000 on the website"},
    {"title": "Insurgent", "section": "Location", "url": "u3",
     "text": "Found at the military base"},
]


# ---------- Exercise 1: clean_text ----------

def test_clean_text_collapses_spaces():
    assert clean_text("The  Kuruma   is fast") == "The Kuruma is fast"


def test_clean_text_removes_edit_markers():
    assert clean_text("Location [edit]") == "Location"


def test_clean_text_removes_templates():
    assert clean_text("Price {{cite web}} $95,000") == "Price $95,000"


def test_clean_text_collapses_blank_lines():
    assert clean_text("a\n\n\n\nb") == "a\n\nb"


def test_clean_text_keeps_single_blank_line():
    assert clean_text("a\n\nb") == "a\n\nb"


def test_clean_text_strips_ends():
    assert clean_text("  padded  ") == "padded"


# ---------- Exercise 2: split_sections ----------

def test_split_sections_basic():
    assert split_sections(SAMPLE_TEXT) == [
        {"heading": "Intro", "text": "The Kuruma is a car."},
        {"heading": "Location", "text": "Found in Rockford Hills."},
        {"heading": "Price", "text": "$95,000"},
    ]


def test_split_sections_no_headings():
    assert split_sections("Just one paragraph.") == [
        {"heading": "Intro", "text": "Just one paragraph."},
    ]


def test_split_sections_drops_empty_sections():
    text = "== Empty ==\n== Story ==\nThe heist begins."
    assert split_sections(text) == [
        {"heading": "Story", "text": "The heist begins."},
    ]


# ---------- Exercise 3: make_chunks ----------

def test_make_chunks_one_per_section():
    chunks = make_chunks(SAMPLE_PAGE)
    assert len(chunks) == 3
    assert chunks[1] == {
        "title": "Kuruma",
        "url": "https://example.wiki/wiki/Kuruma",
        "section": "Location",
        "text": "Found in Rockford Hills.",
    }


def test_make_chunks_splits_long_sections():
    text = "== Story ==\n" + "A" * 300 + "\n\n" + "B" * 300
    page = {"title": "Heist", "url": "u", "text": text}
    chunks = make_chunks(page, max_chars=500)
    assert [c["text"] for c in chunks] == ["A" * 300, "B" * 300]
    assert all(c["section"] == "Story" for c in chunks)


def test_make_chunks_packs_short_paragraphs():
    text = "== Story ==\n" + "A" * 300 + "\n\n" + "B" * 300
    page = {"title": "Heist", "url": "u", "text": text}
    chunks = make_chunks(page, max_chars=1000)
    assert [c["text"] for c in chunks] == ["A" * 300 + "\n\n" + "B" * 300]


# ---------- Exercise 4: save_chunks / load_chunks ----------

def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "chunks.json"
    chunks = make_chunks(SAMPLE_PAGE)
    save_chunks(chunks, path)
    assert load_chunks(path) == chunks


def test_save_keeps_accented_text_readable(tmp_path):
    path = tmp_path / "chunks.json"
    chunks = [{"title": "Señora", "url": "u", "section": "Intro", "text": "café"}]
    save_chunks(chunks, path)
    raw = path.read_text(encoding="utf-8")
    assert "Señora" in raw and "café" in raw


# ---------- Exercise 5: parse_api_response ----------

def test_parse_api_response():
    data = {
        "parse": {
            "title": "Armored Kuruma",
            "pageid": 123,
            "wikitext": "An armored car.\n== Location ==\nLegendary Motorsport.",
        }
    }
    page = parse_api_response(data, "https://example.wiki")
    assert page == {
        "title": "Armored Kuruma",
        "url": "https://example.wiki/wiki/Armored_Kuruma",
        "text": "An armored car.\n== Location ==\nLegendary Motorsport.",
    }


# ---------- Exercise 6: keyword_search ----------

def test_keyword_search_ranks_by_matches():
    # Chunk 0 matches "kuruma" (title) and "location" (section): score 2.
    # Chunks 1 and 2 match one word each: score 1, tie kept in original order.
    result = keyword_search(CHUNKS, "Kuruma location", k=2)
    assert result == [CHUNKS[0], CHUNKS[1]]


def test_keyword_search_ignores_case():
    result = keyword_search(CHUNKS, "MILITARY", k=3)
    assert result == [CHUNKS[2]]


def test_keyword_search_no_match():
    assert keyword_search(CHUNKS, "helicopter", k=3) == []


# ---------- Exercise 7: recall_at_k ----------

GOLDEN = [
    {"question": "q1", "expected_title": "Kuruma", "expected_section": "Location"},
    {"question": "q2", "expected_title": "Insurgent", "expected_section": "Location"},
]


def fake_search(chunks, query, k):
    return chunks[:k]


def test_recall_at_1():
    assert recall_at_k(fake_search, GOLDEN, CHUNKS, k=1) == 0.5


def test_recall_at_3():
    assert recall_at_k(fake_search, GOLDEN, CHUNKS, k=3) == 1.0


def test_recall_empty_golden_set():
    assert recall_at_k(fake_search, [], CHUNKS, k=3) == 0.0
