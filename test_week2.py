"""Week 2 tests for the GTA cheatsheet.

Your code goes in cheatsheet.py, in the same folder.
Run all Week 2 tests:   pytest test_week2.py
Run one exercise:       pytest test_week2.py -k fetch_page

None of these tests touch the internet. Functions that call the wiki take
`get` (and `sleep`) as arguments, and the tests pass in fakes.
"""

import json

from cheatsheet import (
    fetch_page,
    list_category,
    parse_infobox,
    remove_infobox,
    infobox_to_chunk,
    ingest,
    chunk_stats,
    validate_golden,
)

BASE = "https://example.wiki"


# ---------- Fakes ----------

class FakeResponse:
    """Looks like a requests Response: has .json() and .raise_for_status()."""

    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data

    def raise_for_status(self):
        pass


class FakeGet:
    """Stands in for requests.get. Returns canned responses in order and
    records every call so tests can check what was asked for."""

    def __init__(self, *payloads):
        self.payloads = list(payloads)
        self.calls = []

    def __call__(self, url, params=None, headers=None, timeout=None):
        self.calls.append({"url": url, "params": params, "headers": headers})
        return FakeResponse(self.payloads.pop(0))


def api_page(title, wikitext):
    return {"parse": {"title": title, "pageid": 1, "wikitext": wikitext}}


KURUMA_WIKITEXT = (
    "{{Infobox vehicle\n"
    "| name = Kuruma\n"
    "| price = $95,000\n"
    "| class =\n"
    "| manufacturer = Karin\n"
    "}}\n"
    "The Kuruma is a car.\n"
    "== Location ==\n"
    "Found in Rockford Hills."
)


# ---------- Day 1: fetch_page ----------

def test_fetch_page_returns_page_dict():
    get = FakeGet(api_page("Kuruma", "Some text."))
    page = fetch_page("Kuruma", BASE, get=get)
    assert page == {
        "title": "Kuruma",
        "url": "https://example.wiki/wiki/Kuruma",
        "text": "Some text.",
    }


def test_fetch_page_calls_the_api_correctly():
    get = FakeGet(api_page("Kuruma", "Some text."))
    fetch_page("Kuruma", BASE, get=get)
    call = get.calls[0]
    assert call["url"] == "https://example.wiki/api.php"
    assert call["params"] == {
        "action": "parse",
        "page": "Kuruma",
        "prop": "wikitext",
        "format": "json",
        "formatversion": "2",
    }


def test_fetch_page_sends_user_agent():
    get = FakeGet(api_page("Kuruma", "Some text."))
    fetch_page("Kuruma", BASE, get=get)
    headers = get.calls[0]["headers"]
    assert headers is not None and "User-Agent" in headers


# ---------- Day 2: list_category ----------

def test_list_category_single_batch():
    get = FakeGet({
        "query": {"categorymembers": [
            {"title": "Kuruma", "ns": 0},
            {"title": "Insurgent", "ns": 0},
        ]}
    })
    assert list_category("GTA V vehicles", BASE, get=get) == ["Kuruma", "Insurgent"]
    params = get.calls[0]["params"]
    assert params["list"] == "categorymembers"
    assert params["cmtitle"] == "Category:GTA V vehicles"


def test_list_category_follows_continue():
    get = FakeGet(
        {
            "query": {"categorymembers": [{"title": "Kuruma", "ns": 0}]},
            "continue": {"cmcontinue": "page|ABC", "continue": "-||"},
        },
        {
            "query": {"categorymembers": [{"title": "Insurgent", "ns": 0}]},
        },
    )
    titles = list_category("GTA V vehicles", BASE, get=get)
    assert titles == ["Kuruma", "Insurgent"]
    assert len(get.calls) == 2
    assert get.calls[1]["params"]["cmcontinue"] == "page|ABC"


def test_list_category_keeps_only_articles():
    get = FakeGet({
        "query": {"categorymembers": [
            {"title": "Kuruma", "ns": 0},
            {"title": "Category:Sports cars", "ns": 14},
            {"title": "File:Kuruma.png", "ns": 6},
        ]}
    })
    assert list_category("GTA V vehicles", BASE, get=get) == ["Kuruma"]


# ---------- Day 3: parse_infobox / remove_infobox / infobox_to_chunk ----------

def test_parse_infobox():
    assert parse_infobox(KURUMA_WIKITEXT) == {
        "type": "vehicle",
        "fields": {
            "name": "Kuruma",
            "price": "$95,000",
            "manufacturer": "Karin",
        },
    }


def test_parse_infobox_none_when_missing():
    assert parse_infobox("Just text.\n== Location ==\nGarage.") is None


def test_remove_infobox():
    assert remove_infobox(KURUMA_WIKITEXT) == (
        "The Kuruma is a car.\n== Location ==\nFound in Rockford Hills."
    )


def test_remove_infobox_no_infobox_unchanged():
    text = "Just text.\n== Location ==\nGarage."
    assert remove_infobox(text) == text


def test_infobox_to_chunk():
    page = {"title": "Kuruma", "url": "u", "text": KURUMA_WIKITEXT}
    assert infobox_to_chunk(page) == {
        "title": "Kuruma",
        "url": "u",
        "section": "Infobox",
        "text": "name: Kuruma\nprice: $95,000\nmanufacturer: Karin",
    }


def test_infobox_to_chunk_none_when_missing():
    page = {"title": "X", "url": "u", "text": "No box here."}
    assert infobox_to_chunk(page) is None


# ---------- Day 4: ingest ----------

def test_ingest_fetches_caches_and_chunks(tmp_path):
    get = FakeGet(api_page("Kuruma", KURUMA_WIKITEXT))
    sleeps = []
    chunks = ingest(["Kuruma"], BASE, tmp_path, get=get,
                    sleep=sleeps.append, delay=1.5)

    assert [c["section"] for c in chunks] == ["Infobox", "Intro", "Location"]
    assert chunks[0]["text"] == "name: Kuruma\nprice: $95,000\nmanufacturer: Karin"
    assert all(c["title"] == "Kuruma" for c in chunks)

    cached = json.loads((tmp_path / "Kuruma.json").read_text(encoding="utf-8"))
    assert cached["title"] == "Kuruma"
    assert sleeps == [1.5]


def test_ingest_uses_cache_without_network(tmp_path):
    page = {"title": "Kuruma", "url": "https://example.wiki/wiki/Kuruma",
            "text": KURUMA_WIKITEXT}
    (tmp_path / "Kuruma.json").write_text(json.dumps(page), encoding="utf-8")

    get = FakeGet()  # no payloads: any call would crash
    sleeps = []
    chunks = ingest(["Kuruma"], BASE, tmp_path, get=get, sleep=sleeps.append)

    assert len(get.calls) == 0
    assert sleeps == []
    assert len(chunks) == 3


def test_ingest_cache_filename_uses_underscores(tmp_path):
    get = FakeGet(api_page("Armored Kuruma", "Text."))
    ingest(["Armored Kuruma"], BASE, tmp_path, get=get, sleep=lambda s: None)
    assert (tmp_path / "Armored_Kuruma.json").exists()


# ---------- Day 5: chunk_stats ----------

def test_chunk_stats():
    chunks = [
        {"title": "A", "url": "u", "section": "Intro", "text": "abcd"},
        {"title": "A", "url": "u", "section": "Story", "text": "x" * 12},
        {"title": "B", "url": "u", "section": "Intro", "text": "   "},
    ]
    assert chunk_stats(chunks, max_chars=10) == {
        "count": 3,
        "avg_chars": 6.3,
        "empty": 1,
        "too_long": 1,
    }


def test_chunk_stats_empty_list():
    assert chunk_stats([]) == {"count": 0, "avg_chars": 0.0, "empty": 0, "too_long": 0}


# ---------- Day 6: validate_golden ----------

def test_validate_golden_ok():
    golden = [
        {"question": "Where is the Kuruma?", "expected_title": "Kuruma",
         "expected_section": "Location"},
    ]
    assert validate_golden(golden) == []


def test_validate_golden_finds_problems():
    golden = [
        {"question": "Where is the Kuruma?", "expected_title": "Kuruma",
         "expected_section": "Location"},
        {"question": "How much is the Kuruma?", "expected_title": "Kuruma"},
        {"question": "  where is the KURUMA?  ", "expected_title": "Kuruma",
         "expected_section": "Location"},
        {"question": "", "expected_title": "Kuruma", "expected_section": "Intro"},
    ]
    assert validate_golden(golden) == [
        (1, "missing_key"),
        (2, "duplicate_question"),
        (3, "empty_question"),
    ]
