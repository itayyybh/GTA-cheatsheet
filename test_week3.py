"""Week 3 tests for the GTA cheatsheet: embeddings, semantic and hybrid search.

Your code goes in cheatsheet.py, in the same folder.
Run all Week 3 tests:   pytest test_week3.py
Run one exercise:       pytest test_week3.py -k cosine

No test loads a real embedding model. Functions that embed text take
`embed_fn` as an argument (like `get` in Week 2), and the tests pass in fakes
that return tiny hand-made vectors.
"""

import pytest

from cheatsheet import (
    dot,
    norm,
    cosine_similarity,
    chunk_to_embed_text,
    embed_chunks,
    save_index,
    load_index,
    semantic_search,
    make_semantic_search,
    rrf_merge,
    make_hybrid_search,
)


def chunk(title, section, text="t"):
    return {"title": title, "url": "u", "section": section, "text": text}


class FakeEmbed:
    """Stands in for a real model's encode(). Takes a list of texts, returns
    one vector per text from a lookup table, and records every call."""

    def __init__(self, table):
        self.table = table
        self.calls = []

    def __call__(self, texts):
        self.calls.append(list(texts))
        return [self.table[t] for t in texts]


# ---------- Day 1: dot / norm / cosine_similarity ----------

def test_dot():
    assert dot([1, 2, 3], [4, 5, 6]) == 32


def test_norm():
    assert norm([3, 4]) == pytest.approx(5.0)


def test_cosine_same_direction_is_one():
    assert cosine_similarity([1, 2], [2, 4]) == pytest.approx(1.0)


def test_cosine_orthogonal_is_zero():
    assert cosine_similarity([1, 0], [0, 5]) == pytest.approx(0.0)


def test_cosine_opposite_is_minus_one():
    assert cosine_similarity([1, 1], [-2, -2]) == pytest.approx(-1.0)


def test_cosine_zero_vector_is_zero_not_crash():
    assert cosine_similarity([0, 0], [1, 2]) == 0.0


# ---------- Day 2: chunk_to_embed_text / embed_chunks ----------

def test_chunk_to_embed_text():
    c = chunk("Kuruma", "Locations", "Sold at Southern San Andreas Super Autos.")
    assert chunk_to_embed_text(c) == (
        "Kuruma | Locations\nSold at Southern San Andreas Super Autos."
    )


def test_embed_chunks_one_vector_per_chunk_in_order():
    chunks = [chunk("A", "Intro", "a"), chunk("B", "Intro", "b")]
    fake = FakeEmbed({"A | Intro\na": [1, 0], "B | Intro\nb": [0, 1]})
    assert embed_chunks(chunks, fake) == [[1.0, 0.0], [0.0, 1.0]]


def test_embed_chunks_returns_plain_float_lists():
    chunks = [chunk("A", "Intro", "a")]
    fake = FakeEmbed({"A | Intro\na": (3, 4)})   # a tuple of ints, like a numpy row
    vectors = embed_chunks(chunks, fake)
    assert type(vectors[0]) is list
    assert all(type(x) is float for x in vectors[0])


def test_embed_chunks_sends_batches():
    chunks = [chunk(str(i), "S", "x") for i in range(5)]
    fake = FakeEmbed({f"{i} | S\nx": [i, 0] for i in range(5)})
    vectors = embed_chunks(chunks, fake, batch_size=2)
    assert [len(call) for call in fake.calls] == [2, 2, 1]
    assert len(vectors) == 5


# ---------- Day 3: save_index / load_index ----------

def test_index_round_trip(tmp_path):
    path = tmp_path / "index.json"
    chunks = [chunk("A", "Intro", "a")]
    save_index(path, "model-x", chunks, [[0.5, 0.5]])
    assert load_index(path, "model-x") == (chunks, [[0.5, 0.5]])


def test_load_index_wrong_model_raises(tmp_path):
    path = tmp_path / "index.json"
    save_index(path, "model-x", [chunk("A", "Intro")], [[1.0]])
    with pytest.raises(ValueError):
        load_index(path, "model-y")


def test_save_index_length_mismatch_raises(tmp_path):
    with pytest.raises(ValueError):
        save_index(tmp_path / "index.json", "model-x", [chunk("A", "Intro")], [])


# ---------- Day 4: semantic_search / make_semantic_search ----------

CHUNKS = [chunk("Adder", "Infobox"), chunk("Kuruma", "Locations"), chunk("Railgun", "Infobox")]
VECTORS = [[1, 0], [0, 1], [-1, 0]]


def test_semantic_search_ranks_by_cosine():
    results = semantic_search(CHUNKS, VECTORS, [0.9, 0.1], k=3)
    assert [c["title"] for c in results] == ["Adder", "Kuruma", "Railgun"]


def test_semantic_search_respects_k():
    results = semantic_search(CHUNKS, VECTORS, [0.1, 0.9], k=1)
    assert [c["title"] for c in results] == ["Kuruma"]


def test_make_semantic_search_works_with_recall_signature():
    fake = FakeEmbed({"where to buy the kuruma": [0, 2]})
    search = make_semantic_search(VECTORS, fake)
    results = search(CHUNKS, "where to buy the kuruma", 1)   # same call shape as keyword_search
    assert results == [CHUNKS[1]]
    assert fake.calls == [["where to buy the kuruma"]]


# ---------- Day 6: rrf_merge / make_hybrid_search ----------

A, B, C, D = (chunk(x, "S", x) for x in "ABCD")


def test_rrf_merge_rewards_chunks_found_by_both():
    # B is 2nd in both lists, so it beats A and C, which each appear once at rank 1
    merged = rrf_merge([[A, B], [C, B]], k=3)
    assert merged[0] == B
    assert set(c["title"] for c in merged) == {"A", "B", "C"}


def test_rrf_merge_ties_keep_first_seen_order():
    merged = rrf_merge([[A], [C]], k=2)
    assert merged == [A, C]


def test_rrf_merge_same_chunk_from_different_lists_counts_once():
    a_copy = dict(A)   # equal content, different dict object
    merged = rrf_merge([[A, D], [a_copy]], k=5)
    assert len(merged) == 2
    assert merged[0]["title"] == "A"


def test_rrf_merge_score_formula():
    # with c=60: D at rank 1 once = 1/61 ≈ 0.01639; A at rank 2 twice = 2/62 ≈ 0.03226
    merged = rrf_merge([[D, A], [B, A]], k=1, c=60)
    assert merged == [A]


def test_make_hybrid_search_asks_each_search_for_a_pool():
    asked = []

    def search_one(chunks, query, k):
        asked.append(k)
        return [A, B]

    def search_two(chunks, query, k):
        asked.append(k)
        return [B, C]

    hybrid = make_hybrid_search([search_one, search_two], pool=10)
    results = hybrid([A, B, C], "q", 2)
    assert asked == [10, 10]
    assert results[0] == B
    assert len(results) == 2
