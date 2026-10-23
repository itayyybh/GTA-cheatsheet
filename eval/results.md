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
