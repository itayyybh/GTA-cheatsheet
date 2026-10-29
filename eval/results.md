# Retrieval results

Golden set: `golden.json` (31 questions, 19 of 21 pages). Unanswerable questions (`golden_unanswerable.json`, 4) are not part of recall.
A hit = a top-k result with the expected title **and** section. Misses listed by `python baseline.py`.

| Date | Method | k | Chunks | Questions | recall@k | Notes |
|---|---|---:|---:|---:|---:|---|
| 2026-10-18 | `keyword_search` (Week 1, no changes) | 5 | 687 | 31 | 0.516 (16/31) | Baseline |
| 2026-10-18 | `keyword_search` with stopwords | 5 | 687 | 31 | 0.677 (21/31) | |
| 2026-10-18 | `keyword_search` with stopwords and "?" stripped from the word | 5 | 687 | 31 | 0.774 (24/31) | |
| 2026-10-19 | semantic search (`all-MiniLM-L6-v2`, cosine) | 5 | 687 | 31 | 0.774 (24/31) | Ties keyword, but only 2 misses shared; together they miss 2/31 |
| 2026-10-19 | hybrid: keyword + semantic, RRF (c=60, pool=20) | 5 | 687 | 31 | 0.903 (28/31) | +0.129 over either method; ceiling 0.935 (29/31) |

## Baseline misses (2026-10-18) — 15 total

**1. Long chunks win on filler words (~10).** Score = number of distinct question words found, so "how / is / the / what / can / I" count as much as "Adder". Big chunks (`Michael De Santa | Grand Theft Auto V`, `Franklin Clinton | Relationships`, `Personality`) beat the short correct chunk.
Questions: Adder price, Carbonizzare maker, where to buy Kuruma, Complications gold, Franklin and Lamar cars, Franklin special ability, Franklin safehouse, Union Depository gold, Trevor special, ending canon.
→ Try: stopword list in `keyword_search`; later length normalisation / BM25.

**2. Question and page use different words (~3).** "how much" vs `price`, "prize" vs `reward`, "jewelry store" vs "Vangelico".
→ Keyword search can't fix this; embeddings (Week 3).

**3. Right page, wrong section (~3).** Railgun → `Description` (answer in `Infobox`); Insurgent → `Design` (answer in `Variants`); Kuruma off-road → `Kuruma (Armored) | Performance`, which copies the normal Kuruma's text (arguably a correct answer).

**Takeaway:** cleaning fixes C/D would barely move this number — most misses are a scoring problem, not dirty text.

## Keyword vs semantic misses (2026-10-19)

- **Missed by both (2):** jewelry store → Vangelico | Infobox; Complications prize → Infobox.
- **Only keyword missed (5):** Zentorno engine, Franklin and Lamar cars, Carbonizzare maker, ending canon, Trevor special. Semantic fixed all five.
- **Only semantic missed (5):** Adder price, Zentorno price, Railgun unlock, Insurgent pickup, Complications gold.
- **Pattern:** 5 of semantic's 7 misses expect an `Infobox` chunk. Infobox text is `key: value` lines, which doesn't read like a question, so its vector lands far from the question's. Not truncation: all 7 expected chunks are under 900 characters.
- **Ceiling for a combination:** 29/31 = 0.935 if a hybrid kept every hit from either method.
→ Next: hybrid search (RRF, Week 3 Day 6).

## Hybrid misses (2026-10-19) — 3 total
- **Still missed by all:** jewelry store → Vangelico | Infobox.
- **Lost in the merge (2):** Zentorno price (keyword had it), ending canon (semantic had it) — each was found by only one method; likely outscored by chunks that both methods ranked moderately (not yet checked: print each method's rank for the expected chunk).
- **Gained from the pool (1):** Complications prize — in neither method's top 5; likely in both methods' top 20, so its two RRF scores added up to a top-5 finish (not yet checked).

## Holdout check (2026-10-19) — `eval/golden_holdout.json`, 10 questions never used for tuning

| Method | Tuning set (31) | Holdout (10) |
|---|---:|---:|
| keyword (stopwords + "?" strip) | 0.774 | 0.6 (6/10) |
| semantic | 0.774 | 0.7 (7/10) |
| hybrid (RRF) | 0.903 | 0.7 (7/10) |

- All three drop on unseen questions. Keyword drops most — its two fixes were chosen by studying the tuning set's misses.
- Hybrid ties semantic here. With 10 questions, one question = 0.1, so this can't separate hybrid from semantic; it does say 0.903 overstates what to expect.
- Holdout questions were written by Claude while reading the chunks (some vocabulary leak, which favours keyword).

## Holdout v2 (2026-10-23) — 30 questions, most rewritten by Itay in player words

| Method | Tuning set (31) | Holdout v1 (10) | Holdout v2 (30) |
|---|---:|---:|---:|
| keyword (stopwords + "?" strip) | 0.774 | 0.6 | 0.500 (15/30) |
| semantic | 0.774 | 0.7 | 0.767 (23/30) |
| hybrid (RRF) | 0.903 | 0.7 | 0.767 (23/30) |

- Keyword collapses on player wording: its tuning-set score relied on questions that reused the page's words.
- Semantic holds up: 0.774 → 0.767, i.e. no sign it was overfitted.
- Hybrid = semantic on unseen questions. Its +0.129 on the tuning set came from merging with a keyword search that was itself tuned to those questions.
- One question = 0.033 here. Next: compare hybrid vs semantic misses (same score ≠ same misses).

### Holdout v2: semantic vs hybrid misses (2026-10-23)
- **Hybrid fixed 3:** Kuruma AWD, Michael's home town, 100% on Mr. Philips — name-heavy questions where keyword found the page.
- **Hybrid lost 3:** Michael's family fights, where Trevor is from, Freighter practise — descriptive "why/where/what" questions; semantic had them, keyword's poor ranking pulled them out of the top 5.
- **Both missed 4:** Entity XF kind of car (Infobox), Dave Norton at Michael's house, who lives with Franklin (51-char Residents list), repossess in Complications.
- Same score, +3 −3. Any weighting change chosen from these results needs a fresh holdout to judge it.

## "Not documented yet" threshold (2026-10-23) — top semantic cosine per question

- Answerable (holdout v2, 30): 0.44 – 0.80, median ≈ 0.62
- Unanswerable (14): 0.27 – 0.59, median ≈ 0.47
- Overlap: 0.44 – 0.59. No clean gap.

| Threshold | Answerable wrongly refused | Unanswerable wrongly answered |
|---:|---:|---:|
| 0.50 | 1 / 30 | 5 / 14 |
| 0.55 | 2 / 30 | 1 / 14 |
| 0.60 | 12 / 30 | 0 / 14 |

- Candidate: **0.55**. Chosen on these same 44 questions, so it needs checking on new ones before trusting it.
- Note: a high top score only means *some* chunk is close — not that it's the right one (answerable questions that retrieval misses can still score high).


## Answer accuracy — generation (Week 4)

Questions: holdout v2 (30) + unanswerable (14) = 44. Pipeline: 0.55 gate → hybrid top 5 → `build_prompt` → Claude → citation check (`answer_question`).

| Date | Retrieval | Model | Questions | Accuracy (keyword) | Accuracy (by hand) | Claude calls | Tokens in / out | Cost | Avg latency | Notes |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 2026-10-27 | hybrid (RRF), k=5 | claude-haiku-5-5 | 44 | 0.75 (33/44) | ≈ 0.89 (39/44) | 29 | 73,787 / 5,331 | $0.0100 | 1.97 s | Unanswerable 14/14 refused; 5 answerable refused (2 gate, 3 Claude); 6 keyword misses are grader wording misses |
| 2026-10-28 | hybrid (RRF), k=5 | claude-haiku-5-5, prompt v2 (no links, plain text) | 44 | 0.773 (34/44) | ≈ 0.89 (39/44) | 29 | 74,483 / 6,449 | $0.0107 | 1.93 s | No links, no bold; same 5 answerable refusals; +1 keyword pass (#26 now says "central bank") |

- Grader misses (correct answers scored wrong): #7 "based on" vs `inspired`, #8 `explosive`, #17 "all-wheel" vs `all wheel`, #22 other valid reasons, #26 yes/no without `central`, #29 "kills" vs `destroy`.
- Refused answerable: armored Kuruma heist, Franklin's height (gate); Dave Norton, Michael's home town, Freighter practise (Claude). Home town: clean_text deleted the place name ("possibly in the .").
- Problems found by reading: sticky bombs answer gives the GTA IV (TBOGT) price → game filter; Claude invented a gta.fandom.com link → forbid links in the prompt.
- Full answers: Claude Docs "GTA Cheatsheet — Week 4 generation run".

- Prompt v2 (2026-10-28): added "Do not include any links or URLs" and "use plain text no markdown formatting". Fixed both problems; no new refusals. The +0.023 is one question and within run-to-run variation, not a prompt gain.

## Week 5 Day 0 — game traps and the gate fix (2026-10-29)

Trap set: `eval/golden_trap.json` (10 questions, each with a `game`; pages with sections for several games).

| Date | Gate | Set | Accuracy (keyword) | Wrong-game answers | Refused | Claude calls | Cost |
|---|---|---|---:|---:|---|---:|---:|
| 2026-10-29 | `top_score` ≥ 0.55 | trap (10) | 0.6 (6/10) | 0 | 3 gate (#3, #4, #7), 1 Claude (#6) | 7 | — |
| 2026-10-29 | `gate_score` = max(full, `strip_game_words`) ≥ 0.55 | trap (10) | 0.8 (8/10) | 0 | 2 Claude (#3, #6) | 10 | $0.0042 |
| 2026-10-29 | `gate_score` | holdout + unanswerable (44) | 0.705 (31/44) | — | unanswerable 14/14; same 5 answerable as before | 29 | $0.0102 |
| 2026-10-29 | `gate_score`, chunks with heading `path` | trap (10) | 0.8 (8/10) | 0 | 2 Claude (#3, #5) | 10 | $0.0045 |
| 2026-10-29 | `gate_score`, chunks with heading `path` | holdout + unanswerable (44) | 0.75 (33/44); by hand ≈ 0.86 (38/44) | — | unanswerable 14/14; answerable 4 gate, 2 Claude | 27 | $0.0104 |
| 2026-10-29 | `gate_score` ≥ **0.53**, paths | trap (10) | 0.8 (8/10) | 0 | 2 Claude (#3, #5) | 10 | $0.0046 |
| 2026-10-29 | `gate_score` ≥ **0.53**, paths | holdout + unanswerable (44) | 0.795 (35/44); by hand ≈ 0.89 (39/44) | — | unanswerable 14/14; answerable 3 gate, 2 Claude | 28 | $0.0105 |

- Baseline showed **no wrong-game answers**: when the question names the game, hybrid search already finds that game's section. The failures were gate refusals.
- Game words lowered the score for slang ("tbogt" 0.49 → 0.64 stripped, "story mode" 0.54 → 0.61) but raised it for "gta online" (0.79 vs 0.59 stripped), because chunk embeddings include section names like "Grand Theft Auto Online". Hence max of both, not stripping alone.
- Trap misses left (#3 TBoGT missions, #6 Zentorno Online price): tiny list chunks (51 and 57 chars) that lost their heading ("Mission Appearances", "Locations").
- 44-question set: 0.705 vs 0.773 is **grader noise**, not a regression — same refusals, and by hand still ≈ 0.89. 8 keyword misses this run (#7, #8, #16, #17, #22, #26, #29, #30), e.g. "AWD" instead of "all wheel", "killing" instead of "killed". The keyword grader swings by ±3 questions between runs with the same behaviour.
- Fixed my mislabel: trap #10 (sticky bombs in GTA 5) is answerable — Sticky Bombs | Grand Theft Auto V says $400. Holdout #1 still expects the GTA IV price (800); should become Grand Theft Auto V / 400.
- Heading paths (2026-10-29): trap #6 (Zentorno Online $725,000) fixed, the tiny chunk now carries `Locations > Grand Theft Auto Online`. Trap #10 now separates $400 (GTA V) from $800 (TBoGT) on its own. Trap #5 (Buzzard in GTA 6) newly refused by Claude.
- 44-set with paths: unanswerable still 14/14. Answerable refusals 5 → 6: new gate refusal "when is franklin's first safehouse unlocked"; Michael's home town moved from Claude refusal to gate refusal. Every vector changed, so the 0.55 threshold (picked on old vectors) needs re-checking.
- Threshold re-tuned on the path vectors (2026-10-29): sorted `gate_score` over all 44. The groups overlap between 0.51 and 0.57 (highest unanswerable 0.571 "when does GTA 6 come out", which Claude refuses). 0.53 lets in "franklin's first safehouse" (0.542) and no new unanswerable (next is 0.528). Margin is thin (0.014), and the threshold was picked on this same set, so it is slightly optimistic.
- With 0.53: back to the 5 answerable refusals of Week 4 (Kuruma, height, home town at the gate; Dave Norton, freighter by Claude). Dave Norton (0.602) and freighter (0.622) pass the gate easily, so they are retrieval or prompt problems, not gate problems.

- Isolate-the-stage check (2026-10-29), top-5 hybrid for the 4 questions that pass the gate but Claude refuses: **all 4 are retrieval misses**, the answer chunk exists and is clean in every case. Claude refused correctly.
  - Trap #3 TBoGT missions → `Buzzard Attack Chopper | Prominent Appearances in Gameplay > The Ballad of Gay Tony` (51 chars, link list) not in top 5. "tbogt" never matches "The Ballad of Gay Tony".
  - Trap #5 Buzzard in GTA 6 → `Description > Grand Theft Auto VI` not in top 5. "6" never matches "VI".
  - Dave Norton → `Mr. Philips | Description` not in top 5; the question doesn't name the mission, so Michael's page wins.
  - Freighter practise → `The Merryweather Heist | Description > Preparation > Freighter` not in top 5; question says "practise", chunk says "Shooting Range ... improve his shooting skills". `Trivia > Freighter` wins on the heading.
