"""Week 7 tests: fixing typos in names before the gate.

Real questions showed that misspelled names ("trevers", "micheals", "buzard")
crash the gate score (0.30 for "trevers special abilty" vs 0.58 for
"trevor special ability"), so the question is refused before search.
The fix: snap words that are *almost* a known name to that name, before the
gate and the search run.

Your code goes in cheatsheet.py. Run: pytest tests/test_week7.py
Look up difflib.get_close_matches: it finds the closest strings above a
similarity cutoff (0 to 1) and returns [] when nothing is close enough.
"""

import cheatsheet as cs


def chunk(title):
    return {"title": title, "url": "u", "section": "S", "text": "t"}


VOCAB = {"trevor", "michael", "buzzard", "zentorno", "kuruma", "armored",
         "ability", "philips", "sticky", "bombs"}


# ---------- Day 1: title_words ----------

def test_week7_title_words_lowercase_letters_only():
    chunks = [chunk("Trevor Philips"), chunk("Kuruma (Armored)"), chunk("Trevor Philips")]
    assert cs.title_words(chunks) == {"trevor", "philips", "kuruma", "armored"}


def test_week7_title_words_skips_short_words():
    # words shorter than min_len (default 4) are too short to correct safely
    chunks = [chunk("Mr. Philips"), chunk("The Jewel Store Job")]
    assert cs.title_words(chunks) == {"philips", "jewel", "store"}


def test_week7_title_words_ignore():
    # generic title words that would "correct" ordinary words ("story" -> "store")
    chunks = [chunk("The Jewel Store Job"), chunk("Clinton Residence")]
    assert cs.title_words(chunks, ignore={"store", "residence"}) == {"jewel", "clinton"}


# ---------- Day 2: fix_typos ----------

def test_week7_fix_typos_snaps_close_names():
    assert cs.fix_typos("trevers special abilty", VOCAB) == "trevor special ability"
    assert cs.fix_typos("wat guns does the buzard have", VOCAB) == "wat guns does the buzzard have"


def test_week7_fix_typos_lowercases_and_keeps_punctuation():
    assert cs.fix_typos("Whats MICHEALS ability?", VOCAB) == "whats michael ability?"
    assert cs.fix_typos("is the armord kuruma bullet-proof", VOCAB) == "is the armored kuruma bullet-proof"


def test_week7_fix_typos_leaves_correct_and_unrelated_words():
    q = "how much does the zentorno cost in gta online"
    assert cs.fix_typos(q, VOCAB) == q


def test_week7_fix_typos_skips_short_words():
    # "kur" is close-ish to nothing safe; words under min_len are never changed
    assert cs.fix_typos("is kur fast", VOCAB) == "is kur fast"


def test_week7_fix_typos_cutoff():
    # "trevers" vs "trevor" is about 0.77 similar: fixed at 0.75, not at 0.9
    assert cs.fix_typos("trevers", VOCAB, cutoff=0.75) == "trevor"
    assert cs.fix_typos("trevers", VOCAB, cutoff=0.9) == "trevers"


def test_week7_fix_typos_empty_vocabulary():
    assert cs.fix_typos("trevers special", set()) == "trevers special"


# ---------- Day 3: check_rate (rate limiting, pure) ----------
# `times` = the request times (seconds) one visitor already made.
# Returns (allowed, kept): kept = the times still inside the window,
# plus `now` if the request is allowed. A time counts while it is > now - window.

def test_week7_check_rate_under_limit():
    assert cs.check_rate([], 100.0, 2) == (True, [100.0])
    assert cs.check_rate([100.0], 101.0, 2) == (True, [100.0, 101.0])


def test_week7_check_rate_at_limit_blocks_and_does_not_add():
    assert cs.check_rate([100.0, 101.0], 102.0, 2) == (False, [100.0, 101.0])


def test_week7_check_rate_old_requests_expire():
    assert cs.check_rate([10.0, 20.0], 100.0, 2) == (True, [100.0])
    assert cs.check_rate([40.0], 100.0, 1) == (True, [100.0])        # exactly 60 s old: expired
    assert cs.check_rate([41.0], 100.0, 1) == (False, [41.0])        # 59 s old: still counts


def test_week7_check_rate_custom_window():
    assert cs.check_rate([95.0], 100.0, 1, window=10.0) == (False, [95.0])
    assert cs.check_rate([85.0], 100.0, 1, window=10.0) == (True, [100.0])
