"""Week 5 tests for the GTA cheatsheet: the game filter.

Your code goes in cheatsheet.py. Run from the project root:
    pytest -k week5                    all Week 5 tests
    pytest -k section_games            one exercise

Game codes used everywhere: "IV", "V", "Online", "VI", plus "all" for a chunk
that has no game clue (it applies to every game).

The tests call functions as `cs.name(...)`, so a function you haven't written
yet only fails its own tests. No placeholders needed.
"""

import cheatsheet as cs


def chunk(title, section, text="t", games=None):
    c = {"title": title, "url": "u", "section": section, "text": text}
    if games is not None:
        c["games"] = games
    return c


class FakeEmbed:
    def __init__(self, table):
        self.table = table

    def __call__(self, texts):
        return [self.table[t] for t in texts]


# ---------- Day 1: section_games / infobox_games ----------
# Section names below are real ones from your chunks.json.

def test_week5_section_games_single_game():
    assert cs.section_games("Grand Theft Auto V") == ["V"]
    assert cs.section_games("Grand Theft Auto Online") == ["Online"]
    assert cs.section_games("Grand Theft Auto VI") == ["VI"]


def test_week5_section_games_vi_is_not_v():
    # "Grand Theft Auto V" is inside "Grand Theft Auto VI" as text — a classic trap
    assert "V" not in cs.section_games("Grand Theft Auto VI")


def test_week5_section_games_two_games():
    assert cs.section_games("Grand Theft Auto V and Online") == ["V", "Online"]
    assert cs.section_games("GTA V and Online Overview") == ["V", "Online"]


def test_week5_section_games_short_names_and_tbogt():
    assert cs.section_games("GTA Online: Import/Export") == ["Online"]
    assert cs.section_games("GTA V Overview") == ["V"]
    assert cs.section_games("TBoGT Overview") == ["IV"]
    assert cs.section_games("The Ballad of Gay Tony") == ["IV"]


def test_week5_section_games_inside_longer_names():
    assert cs.section_games("Events of Grand Theft Auto V") == ["V"]
    assert cs.section_games("Grand Theft Auto Online in 2013") == ["Online"]


def test_week5_section_games_no_game():
    assert cs.section_games("Performance") == []
    assert cs.section_games("HD Universe") == []


def test_week5_infobox_games_plain():
    text = "name: Adder\ngames: {{games|V=y|O=y}}\nprice: $1,000,000"
    assert cs.infobox_games(text) == ["V", "Online"]


def test_week5_infobox_games_tbogt_and_vi():
    text = "games: {{Games|TBOGT=y|V=y|O=y|VI=y}}"
    assert cs.infobox_games(text) == ["IV", "V", "Online", "VI"]


def test_week5_infobox_games_value_is_not_just_y():
    # real data: a DLC template instead of "y" still means the game has it
    text = "games: {{Games|O={{DLC|mpheist}}}}"
    assert cs.infobox_games(text) == ["Online"]


def test_week5_infobox_games_missing():
    assert cs.infobox_games("name: Something\nprice: $5") == []


# ---------- Day 2: chunk_games / add_games / count_by_game ----------

def test_week5_chunk_games_uses_section():
    assert cs.chunk_games(chunk("Adder", "Grand Theft Auto Online")) == ["Online"]


def test_week5_chunk_games_uses_infobox_field():
    c = chunk("Adder", "Infobox", "games: {{games|V=y|O=y}}")
    assert cs.chunk_games(c) == ["V", "Online"]


def test_week5_chunk_games_no_clue_means_all():
    assert cs.chunk_games(chunk("Adder", "Performance")) == ["all"]


def test_week5_add_games_adds_field_without_changing_input():
    original = [chunk("Adder", "Grand Theft Auto V"), chunk("Adder", "Design")]
    result = cs.add_games(original)
    assert [c["games"] for c in result] == [["V"], ["all"]]
    assert "games" not in original[0]          # input list untouched
    assert result[0]["text"] == "t"            # other fields kept


def test_week5_count_by_game_counts_every_game_of_a_chunk():
    chunks = [chunk("A", "S", games=["V", "Online"]), chunk("B", "S", games=["V"]),
              chunk("C", "S", games=["all"])]
    assert cs.count_by_game(chunks) == {"V": 2, "Online": 1, "all": 1}


# ---------- Day 3: matches_game / filter_by_game ----------

def test_week5_matches_game():
    assert cs.matches_game(chunk("A", "S", games=["V", "Online"]), "Online") is True
    assert cs.matches_game(chunk("A", "S", games=["IV"]), "V") is False
    assert cs.matches_game(chunk("A", "S", games=["all"]), "VI") is True


def test_week5_filter_by_game_keeps_chunks_and_vectors_paired():
    chunks = [chunk("A", "S", games=["IV"]), chunk("B", "S", games=["V"]),
              chunk("C", "S", games=["all"])]
    vectors = [[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]]
    kept_chunks, kept_vectors = cs.filter_by_game(chunks, vectors, "V")
    assert [c["title"] for c in kept_chunks] == ["B", "C"]
    assert kept_vectors == [[0.0, 1.0], [0.5, 0.5]]


def test_week5_filter_by_game_none_keeps_everything():
    chunks = [chunk("A", "S", games=["IV"])]
    assert cs.filter_by_game(chunks, [[1.0]], None) == (chunks, [[1.0]])


# ---------- Day 4: detect_game ----------

def test_week5_detect_game_online():
    assert cs.detect_game("how do i get the oppressor in gta online") == "Online"


def test_week5_detect_game_gta6_spellings():
    assert cs.detect_game("when does GTA 6 come out") == "VI"
    assert cs.detect_game("gta vi map size") == "VI"


def test_week5_detect_game_gta4():
    assert cs.detect_game("buzzard price in tbogt") == "IV"
    assert cs.detect_game("is the adder in gta 4") == "IV"


def test_week5_detect_game_gta_v_not_confused_with_vi():
    assert cs.detect_game("gta v adder price") == "V"
    assert cs.detect_game("story mode heists") == "V"


def test_week5_detect_game_default():
    assert cs.detect_game("how much is the adder") == "V"
    assert cs.detect_game("how much is the adder", default=None) is None


# ---------- Day 5: make_game_search ----------

def test_week5_make_game_search_only_returns_that_game():
    chunks = [
        chunk("Buzzard", "TBoGT Overview", "buzzard price 100", games=["IV"]),
        chunk("Buzzard", "GTA V Overview", "buzzard price 200", games=["V"]),
        chunk("Buzzard", "Intro", "buzzard helicopter", games=["all"]),
    ]
    vectors = [[1.0, 0.0], [0.9, 0.1], [0.0, 1.0]]
    embed = FakeEmbed({"buzzard price": [1.0, 0.0]})
    game_chunks, search = cs.make_game_search(chunks, vectors, "V", embed, pool=5)
    assert [c["section"] for c in game_chunks] == ["GTA V Overview", "Intro"]
    results = search(game_chunks, "buzzard price", 2)
    assert all(cs.matches_game(c, "V") for c in results)
    assert results[0]["section"] == "GTA V Overview"


# ---------- Day 4b: strip_game_words (gate fix) ----------
# The game words go to detect_game; the rest is what gets scored and searched.

def test_week5_strip_game_words_removes_in_plus_game():
    assert cs.strip_game_words("which missions use the buzzard in tbogt") == "which missions use the buzzard"
    assert cs.strip_game_words("where do i get the zentorno in story mode") == "where do i get the zentorno"


def test_week5_strip_game_words_gta_spellings():
    assert cs.strip_game_words("how much does the zentorno cost in gta online") == "how much does the zentorno cost"
    assert cs.strip_game_words("is the buzzard in gta 6") == "is the buzzard"
    assert cs.strip_game_words("gta v adder price") == "adder price"


def test_week5_strip_game_words_leaves_other_questions_alone():
    assert cs.strip_game_words("how much is the adder") == "how much is the adder"


def test_week5_strip_game_words_does_not_eat_parts_of_words():
    # "gta v" must not be cut out of "gta vice city"
    assert cs.strip_game_words("gta vice city map") == "gta vice city map"
