# Retrieval results

Golden set: `golden.json` (31 questions, 19 of 21 pages). Unanswerable questions (`golden_unanswerable.json`, 4) are not part of recall.
A hit = a top-k result with the expected title **and** section. Misses listed by `python baseline.py`.

| Date | Method | k | Chunks | Questions | recall@k | Notes |
|---|---|---:|---:|---:|---:|---|
| 2026-18-10 | `keyword_search` (Week 1, no changes) | 5 | 687 | 31 | 0.516 (16/31) | Baseline |
| 2026-18-10 | `keyword_search` with stopwords | 5 | 687 | 31 | 0.677 (21/31)
| 2026-18-10 | `keyword_search` with stopwords and "?" stripped from the word | 5 | 687 | 31 | 0.774 (24/31) | 

## Baseline misses (2026-10-18) — 15 total

**1. Long chunks win on filler words (~10).** Score = number of distinct question words found, so "how / is / the / what / can / I" count as much as "Adder". Big chunks (`Michael De Santa | Grand Theft Auto V`, `Franklin Clinton | Relationships`, `Personality`) beat the short correct chunk.
Questions: Adder price, Carbonizzare maker, where to buy Kuruma, Complications gold, Franklin and Lamar cars, Franklin special ability, Franklin safehouse, Union Depository gold, Trevor special, ending canon.
→ Try: stopword list in `keyword_search`; later length normalisation / BM25.

**2. Question and page use different words (~3).** "how much" vs `price`, "prize" vs `reward`, "jewelry store" vs "Vangelico".
→ Keyword search can't fix this; embeddings (Week 3).

**3. Right page, wrong section (~3).** Railgun → `Description` (answer in `Infobox`); Insurgent → `Design` (answer in `Variants`); Kuruma off-road → `Kuruma (Armored) | Performance`, which copies the normal Kuruma's text (arguably a correct answer).

**Takeaway:** cleaning fixes C/D would barely move this number — most misses are a scoring problem, not dirty text.
