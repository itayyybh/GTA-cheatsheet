"""Week 4 tests for the GTA cheatsheet: grounded generation with citations.

Your code goes in cheatsheet.py. Run from the project root:
    pytest -k week4                    all Week 4 tests
    pytest -k format_context           one exercise

No test calls a real model. Functions that need the LLM take `llm_fn` as an
argument (like `embed_fn` in Week 3): a function that takes one prompt string
and returns the model's reply as a string. The tests pass in fakes.

The tests call functions as `cs.name(...)`, so a function you haven't written
yet only fails its own tests. No placeholders needed.
"""

import cheatsheet as cs


def chunk(title, section, text="t", url="u"):
    return {"title": title, "url": url, "section": section, "text": text}


ADDER = chunk("Adder", "Infobox", "price: $1,000,000", "https://gta.wiki/wiki/Adder")
KURUMA = chunk("Kuruma", "Locations", "Sold at Southern San Andreas Super Autos.", "https://gta.wiki/wiki/Kuruma")
RAILGUN = chunk("Railgun", "Description", "Fires rounds using electromagnetism.", "https://gta.wiki/wiki/Railgun")

REFUSAL = "Not documented yet."


class FakeLLM:
    """Stands in for a Claude call. Returns a fixed reply and records every prompt."""

    def __init__(self, reply):
        self.reply = reply
        self.prompts = []

    def __call__(self, prompt):
        self.prompts.append(prompt)
        return self.reply


class FakeSearch:
    """Returns fixed chunks and records the k it was asked for."""

    def __init__(self, results):
        self.results = results
        self.ks = []

    def __call__(self, chunks, query, k):
        self.ks.append(k)
        return self.results[:k]


# ---------- Day 1: format_context / build_prompt ----------

def test_week4_format_context_numbers_sources_from_one():
    assert cs.format_context([ADDER, KURUMA]) == (
        "[1] Adder | Infobox\nprice: $1,000,000\n\n"
        "[2] Kuruma | Locations\nSold at Southern San Andreas Super Autos."
    )


def test_week4_format_context_empty():
    assert cs.format_context([]) == ""


def test_week4_build_prompt_contains_context_and_question():
    prompt = cs.build_prompt("how much is the adder", [ADDER, KURUMA])
    assert cs.format_context([ADDER, KURUMA]) in prompt
    assert "how much is the adder" in prompt


def test_week4_build_prompt_puts_question_after_sources():
    prompt = cs.build_prompt("how much is the adder", [ADDER])
    assert prompt.index("how much is the adder") > prompt.index("[1] Adder | Infobox")


def test_week4_build_prompt_explains_refusal_and_citations():
    prompt = cs.build_prompt("q", [ADDER])
    assert "NOT_DOCUMENTED" in prompt     # the exact word the model must reply with
    assert "[1]" in prompt                # sources are cited by their number


# ---------- Day 2: should_answer ----------

def test_week4_should_answer_above_threshold():
    assert cs.should_answer(0.70) is True


def test_week4_should_answer_below_threshold():
    assert cs.should_answer(0.40) is False


def test_week4_should_answer_exactly_threshold():
    assert cs.should_answer(0.55) is True


def test_week4_should_answer_custom_threshold():
    assert cs.should_answer(0.60, threshold=0.65) is False


# ---------- Day 3: parse_citations / valid_citations ----------

def test_week4_parse_citations_first_seen_order_no_repeats():
    assert cs.parse_citations("Costs $1M [2]. Sold online [1][2].") == [2, 1]


def test_week4_parse_citations_none():
    assert cs.parse_citations("No sources here.") == []


def test_week4_parse_citations_multi_digit_and_ignores_non_numbers():
    assert cs.parse_citations("See [12] and [a] and [x1].") == [12]


def test_week4_valid_citations_drops_numbers_outside_sources():
    assert cs.valid_citations([0, 2, 7, 3], n_sources=3) == [2, 3]


# ---------- Day 4: cited_sources ----------

def test_week4_cited_sources_in_citation_order():
    assert cs.cited_sources([3, 1], [ADDER, KURUMA, RAILGUN]) == [
        {"n": 3, "title": "Railgun", "section": "Description", "url": "https://gta.wiki/wiki/Railgun"},
        {"n": 1, "title": "Adder", "section": "Infobox", "url": "https://gta.wiki/wiki/Adder"},
    ]


def test_week4_cited_sources_empty():
    assert cs.cited_sources([], [ADDER]) == []


# ---------- Day 5: answer_question ----------

def answer(llm, score=0.9, results=(ADDER, KURUMA), k=5):
    search = FakeSearch(list(results))
    result = cs.answer_question(
        "how much is the adder", [ADDER, KURUMA, RAILGUN],
        search_fn=search, score_fn=lambda q: score, llm_fn=llm, k=k,
    )
    return result, search


def test_week4_answer_question_happy_path():
    llm = FakeLLM("  The Adder costs $1,000,000 [1].  ")
    result, _ = answer(llm)
    assert result == {
        "answer": "The Adder costs $1,000,000 [1].",
        "sources": [{"n": 1, "title": "Adder", "section": "Infobox", "url": "https://gta.wiki/wiki/Adder"}],
        "refused": False,
    }


def test_week4_answer_question_low_score_refuses_without_calling_llm():
    llm = FakeLLM("should never be used [1]")
    result, _ = answer(llm, score=0.30)
    assert result == {"answer": REFUSAL, "sources": [], "refused": True}
    assert llm.prompts == []              # no model call = no cost


def test_week4_answer_question_model_says_not_documented():
    result, _ = answer(FakeLLM("NOT_DOCUMENTED"))
    assert result == {"answer": REFUSAL, "sources": [], "refused": True}


def test_week4_answer_question_answer_without_valid_citation_is_refused():
    # [9] doesn't exist among the sources: an unsupported answer is not shown
    result, _ = answer(FakeLLM("The Adder costs $5 [9]."))
    assert result == {"answer": REFUSAL, "sources": [], "refused": True}


def test_week4_answer_question_passes_k_and_sends_question():
    llm = FakeLLM("Sold at Super Autos [2].")
    result, search = answer(llm, k=2)
    assert search.ks == [2]
    assert len(llm.prompts) == 1 and "how much is the adder" in llm.prompts[0]
    assert result["sources"][0]["title"] == "Kuruma"


# ---------- Day 6: answer_matches / score_answers ----------

def test_week4_answer_matches_all_required_case_insensitive():
    assert cs.answer_matches("The Adder costs $1,000,000 [1].", ["adder", "1,000,000"]) is True


def test_week4_answer_matches_missing_one():
    assert cs.answer_matches("The Adder is fast.", ["adder", "1,000,000"]) is False


def test_week4_score_answers():
    golden = [
        {"question": "q1", "must_contain": ["1,000,000"]},          # answered correctly
        {"question": "q2", "must_contain": ["super autos"]},        # answered, wrong content
        {"question": "q3", "unanswerable": True},                   # correctly refused
        {"question": "q4", "unanswerable": True},                   # answered: wrong
    ]
    replies = {
        "q1": {"answer": "It costs $1,000,000 [1].", "sources": [], "refused": False},
        "q2": {"answer": "It is fast [1].", "sources": [], "refused": False},
        "q3": {"answer": REFUSAL, "sources": [], "refused": True},
        "q4": {"answer": "Made up [1].", "sources": [], "refused": False},
    }
    assert cs.score_answers(golden, lambda q: replies[q]) == 0.5
