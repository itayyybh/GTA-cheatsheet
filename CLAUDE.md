I'm relearning Python. Never write or edit code in cheatsheet.py. Only give hints, review my code, and run the tests.

# Python Refresher — GTA Cheatsheet

## Who I am and how to help
- I knew Python well years ago and am relearning it; this is recall, not starting from zero.
- I write every line of `cheatsheet.py` myself. Never write, edit or paste a solution for it, even if I'm stuck.
- When I'm stuck, give the smallest hint that unblocks me: point at the line, name the concept or method, show a tiny example on unrelated data. Not the fix.
- Reviews: list bugs most important first, say why each one fails, and what to look up. Mention what's already right.
- Keep answers short and in English.
- You may run tests: `pytest -k <function_name>` for one exercise, `pytest` for everything (run from the project root; `pytest.ini` points it at `tests/`). Explain failures by reading the assertion (left side = my output, right side = expected).
- Never change the test files.

## The project
A GTA "AI cheatsheet": a RAG question-answering system over wiki pages. GTA V data now, GTA 6 data after its launch on November 19, 2026.

- `tests/test_cheatsheet.py` — Week 1 spec (21 tests)
- `tests/test_week2.py` — Week 2 spec (19 tests). Uses fakes for `get` and `sleep`, so no test touches the internet.
- `cheatsheet.py` — my code
- Week 1 plan: https://claude.ai/code/artifact/c2bf4f46-e812-410c-a096-992d9e9b3cf8
- Week 2 plan: https://claude.ai/code/artifact/b8402308-5372-472d-81cf-a6b6b3b1877c
- Week 3 plan: https://claude.ai/code/artifact/429301dc-9d6a-470b-9637-3d19773f08a4
- `tests/test_week3.py` — Week 3 spec (21 tests). Uses a fake `embed_fn`, so no test loads a model.
- `tests/test_week4.py` — Week 4 spec (23 tests). Uses a fake `llm_fn`, so no test calls Claude.
- `tests/test_week5.py` — Week 5 spec (37 tests): game filter, `strip_game_words`, heading paths.
- `tests/test_week6.py` + `tests/test_week6_app.py` — Week 6 spec (15 + 7 tests): logging, validation, the FastAPI app.
- Architecture: https://claude.ai/code/artifact/826846de-0508-4d53-be1a-1eee1a5e837f

## Folder layout
- `cheatsheet.py` — my code (tests import it from the root)
- `runs/` — real-data scripts (`week3_run.py`, `week4_run.py`, `week5_run.py`, `rebuild_chunks.py`). Run them from the project root as modules: `python -m runs.week5_run` (no `.py`). `-m` keeps the root on the import path, so `from cheatsheet import ...` and the relative `data/` and `eval/` paths still work. `python runs/week5_run.py` fails with `ModuleNotFoundError: cheatsheet`.
- `tests/` — the spec files (never edit); `pytest.ini` sets `pythonpath = .` so they find `cheatsheet.py`
- `data/` — `raw/` (hand-saved wikitext) → `cache/` (page dicts) → `chunks.json`; `index.json` = embeddings, git-ignored, delete it to rebuild
- `eval/` — `golden.json`, `golden_holdout.json`, `golden_unanswerable.json`, `golden_trap.json`, `results.md` (every score, dated)
- `notes/` — `cleaning_notes.md`, `LEARN.md` (💡 Learn glossary)

## Data source rules
- Do NOT use Fandom (gta.fandom.com): its terms ban automated access, and the GTA Wiki community left it for gta.wiki in March 2026.
- gta.wiki (main GTA Wiki, ~24k articles): text is CC BY-NC-SA 3.0 (attribution, non-commercial, share-alike). Its host Weird Gloop's terms forbid automated use without prior consent. **Declined 2026-10-28** (Cook, Weird Gloop, on Discord): they no longer vet projects that use the wiki as a backend. So no script ever hits gta.wiki — no API calls, no scraping.
- Grand Theft Wiki (grandtheftwiki.com): text is CC BY-SA 3.0. Bot/API rules not stated; ask staff before scripting it.
- Until I have permission: save pages by hand in the browser (raw wikitext) into the cache folder as page dicts. `ingest` reads the cache and never calls the network for cached pages.
- Every answer must link back to the source page (attribution is required by both licenses).

## Week 1 (done)
`clean_text`, `split_sections`, `make_chunks`, `save_chunks` / `load_chunks`, `parse_api_response`, `keyword_search`, `recall_at_k` — 21/21 passing.

## Week 2 exercises
1. `fetch_page(title, base_url, get=requests.get)` — GET `base_url + "/api.php"` with params `action=parse`, `page`, `prop=wikitext`, `format=json`, `formatversion=2`; send a `User-Agent` header and a `timeout`; call `raise_for_status()`, then pass `.json()` to `parse_api_response`.
2. `list_category(category, base_url, get=requests.get)` — params `action=query`, `list=categorymembers`, `cmtitle=Category:<category>`, `cmlimit=500`, `format=json`, `formatversion=2`; keep members with `ns == 0`; follow `data["continue"]["cmcontinue"]` by passing it back as a `cmcontinue` param until there's no `continue`.
3. `parse_infobox(wikitext)` — box starts at a line beginning `{{Infobox <type>`, ends at a line that is just `}}`; fields are `| key = value` lines (split on the first `=`); skip empty values; return `{"type", "fields"}` or `None`. `remove_infobox(wikitext)` — text without those lines, stripped; unchanged if none. `infobox_to_chunk(page)` — chunk with section `"Infobox"`, text `key: value` lines in order, or `None`.
4. `ingest(titles, base_url, cache_dir, get=requests.get, sleep=time.sleep, delay=1.0)` — cache file is `cache_dir / (title with spaces → underscores + ".json")`; if it exists load it (no fetch, no sleep); else `fetch_page`, save the page dict, `sleep(delay)`. Chunks per page: infobox chunk first (if any), then `make_chunks` on text `clean_text(remove_infobox(text))`. Real run: ~20 hand-saved pages in the cache (see Data source rules) → `ingest` → `save_chunks`.
5. `chunk_stats(chunks, max_chars=1000)` — `count`, `avg_chars` (rounded to 1 decimal), `empty` (whitespace-only text), `too_long` (> `max_chars`); empty list gives zeros with `avg_chars` `0.0`. Then eyeball 20 random chunks and list cleaning problems.
6. `golden.json` — 30 real player questions with `question`, `expected_title`, `expected_section`, incl. 3–4 unanswerable. Questions must be answerable from the pages actually ingested. `validate_golden(items)` returns `(index, problem)` tuples: `"missing_key"`, `"empty_question"`, `"duplicate_question"` (case- and space-insensitive); `[]` when valid.
7. Baseline: `recall_at_k(keyword_search, golden, chunks, k=5)` on real data; record the number with the date and study the misses.

## Week 3 exercises (embeddings, semantic + hybrid search)
Model: `all-MiniLM-L6-v2` via `sentence-transformers`, loaded only in scripts (never imported in `cheatsheet.py`). `embed_fn(list_of_texts) -> one vector per text`.
1. `dot(a, b)`, `norm(a)`, `cosine_similarity(a, b)` — plain Python; cosine returns `0.0` if either vector is all zeros.
2. `chunk_to_embed_text(chunk)` → `"<title> | <section>\n<text>"`. `embed_chunks(chunks, embed_fn, batch_size=32)` — calls `embed_fn` per batch, returns one plain list of floats per chunk, in order.
3. `save_index(path, model, chunks, vectors)` — JSON `{"model","chunks","vectors"}`, `ValueError` if lengths differ. `load_index(path, model)` → `(chunks, vectors)`, `ValueError` if the model name differs.
4. `semantic_search(chunks, vectors, query_vector, k)` — top k by cosine. `make_semantic_search(vectors, embed_fn)` → closure `search(chunks, query, k)` usable with `recall_at_k`.
5. Real run (`week3_run.py`, no tests): build/load `index.json`, recall@5 keyword vs semantic, print misses, row in `results.md`. MiniLM truncates long texts (~256 words).
6. `rrf_merge(result_lists, k, c=60)` — sum of `1/(c+rank)`, rank from 1; chunk identity = `(title, section, text)`; ties keep first-seen order. `make_hybrid_search(search_fns, pool=20)` → closure that asks each search for `pool` results and merges. Then recall@5 for hybrid.
7. No tests: `golden_holdout.json` (10 new untuned questions) scored by all three methods; top semantic score for answerable vs unanswerable questions → candidate "not documented yet" threshold.

## Week 4 exercises (generation with citations)
Tests: `tests/test_week4.py` (23 tests). They call `cs.name(...)`, so no placeholders are needed — an unwritten function only fails its own tests. `llm_fn(prompt) -> reply string` is injected; the real Claude call lives only in `week4_run.py`, never in `cheatsheet.py`.
1. `format_context(chunks)` → `"[1] <title> | <section>\n<text>"` blocks joined by a blank line; `""` for no chunks. `build_prompt(question, chunks)` → instructions + context + question (question after the sources); must mention `NOT_DOCUMENTED` and citing like `[1]`.
2. `should_answer(score, threshold=0.55)` → `score >= threshold`.
3. `parse_citations(text)` → ints from `[n]`, first-seen order, no repeats. `valid_citations(cited, n_sources)` → only 1..n_sources, order kept.
4. `cited_sources(cited, chunks)` → `[{"n", "title", "section", "url"}]` in citation order.
5. `answer_question(question, chunks, search_fn, score_fn, llm_fn, k=5, threshold=0.55)` → `{"answer", "sources", "refused"}`. Refuse with `"Not documented yet."` (no LLM call) below threshold; also refuse if the reply contains `NOT_DOCUMENTED` or has no valid citation. Otherwise answer = reply stripped.
6. `answer_matches(answer, must_contain)` (all, case-insensitive). `score_answers(golden, answer_fn)` → fraction correct: answerable items need not refused + match; `"unanswerable": True` items need refused.
7. Real run (`week4_run.py`, no tests): Claude via the Anthropic SDK, holdout + unanswerable with `must_contain` added, answer accuracy, tokens/cost and latency per question, row in `eval/results.md`.

## Week 5 exercises (game filter)
Tests: `tests/test_week5.py` (24 tests), called as `cs.name(...)` — no placeholders needed. Game codes: "IV", "V", "Online", "VI", and "all" (no game clue).
0. No tests: ~10 trap questions with a `game` field (pages with several games: Buzzard, Sticky Bombs, Adder…); run the current pipeline and record wrong-game answers as the baseline.
1. `section_games(section)` → games named in a section heading ("Grand Theft Auto V and Online" → ["V", "Online"]; "TBoGT Overview" → ["IV"]; "Grand Theft Auto VI" must not count as V). `infobox_games(text)` → from the `games: {{Games|TBOGT=y|V=y|O=…}}` line; any value counts, not only `y`; keys TBOGT/TLAD/IV → "IV", O → "Online".
2. `chunk_games(chunk)` → infobox field for Infobox chunks, else the section; nothing found → ["all"]. `add_games(chunks)` → new chunks with a `games` field, input unchanged. `count_by_game(chunks)` → {game: count}. Then re-ingest and rebuild `data/index.json`.
3. `matches_game(chunk, game)` (its game or "all"). `filter_by_game(chunks, vectors, game)` → both lists filtered together, kept paired; `None` → unchanged.
4. `detect_game(question, default="V")` → "VI" (gta 6 / gta vi), "Online", "IV" (gta 4 / tbogt / gay tony), "V" (gta v / gta 5 / story mode), else default. "gta vi" must not match V.
5. `make_game_search(chunks, vectors, game, embed_fn, pool=20)` → (game_chunks, hybrid search over only that game's chunks). Then re-run the trap set and the 44-question eval.
Measured 2026-10-28 with a reference version: 489 of 687 chunks have no game clue ("all"); V 136, Online 71, IV 17, VI 7. Subsections lose their parent heading, which limits the filter.

### Week 5 path fix (tiny chunks lose their parent heading)
Tests in `tests/test_week5.py` (P1–P3, 9 tests). `section` stays unchanged so golden sets and old tests keep working; a new `path` field carries the full heading path.
- P1 `heading_level(line)` → number of leading `=` (0 if not a heading). `split_sections_with_path(text)` → `[{"heading", "path", "text"}]`, path like "Locations > Grand Theft Auto Online"; a heading at level n replaces everything at level ≥ n; empty sections dropped but still count as parents.
- P2 `make_path_chunks(page, max_chars=1000)` → same chunks as `make_chunks` plus `path` (skip list on `heading`, like `make_chunks`).
- P3 `chunk_label(chunk)` → `path` if present, else `section`. Use it in `chunk_to_embed_text` and `format_context`.
- Then: `ingest` uses `make_path_chunks`, rebuild `data/chunks.json` and delete `data/index.json` so it re-embeds; re-run trap + 44-question sets.
- Checked 2026-10-29 with a reference version on the real cache: still 687 chunks, identical apart from `path`; 494 get a parent in their path. Trap misses #3 → "Prominent Appearances in Gameplay > The Ballad of Gay Tony", #6 → "Locations > Grand Theft Auto Online".

### Week 6 — web page + logging (go/no-go 2026-11-13)
Decided 2026-11-01: FastAPI + one HTML page; run locally first, decide on 2026-11-13 whether to deploy (non-commercial, with attribution).
Tests: `tests/test_week6.py` (15 tests, helpers in `cheatsheet.py`) and `tests/test_week6_app.py` (7 tests, `app.py`; skipped until `pip install fastapi uvicorn httpx`).
1. `log_entry(question, result, game, seconds, when, error=None)` → `{time, question, game, refused, answer, sources (urls), seconds (2 dp), error}`. `append_jsonl(path, entry)` → one JSON line, `ensure_ascii=False`, creates the parent folder. `read_jsonl(path)` → list, skips blank lines, missing file → `[]`.
2. `log_summary(entries)` → `{count, refused, refusal_rate (3 dp), errors, avg_seconds (2 dp), by_game}`; game `None` counts as `"none"`; empty → zeros and `{}`.
3. `validate_question(text, max_chars=300)` → `(stripped, None)`, `(None, "empty")` or `(None, "too_long")`. `source_links(sources)` → `[{title, url}]`, one per page (url), first-cited order — the attribution both licenses require.
4. `app.py`: `create_app(answer_fn, log_path)` returns a FastAPI app. `GET /` → HTML page with a form. `POST /ask` with JSON `{"question"}` → `{answer, refused, game, sources}` (sources via `source_links`, `game` from `result.get("game")`); bad question → 400 `{"error": "empty" | "too_long"}` without calling `answer_fn`.
5. Every answered question appends a `log_entry` (time = UTC ISO string, seconds measured around `answer_fn`). If `answer_fn` raises → 503 `{"error": "model_unavailable"}` and a logged entry with `refused: True` and `error` = the exception's class name. `GET /stats` → `log_summary` of the log.
6. Real run (no tests): `runs/serve.py` builds the real `answer_fn` (index, model, gate, `answer_with_game` + game) and starts uvicorn; log to `logs/questions.jsonl` (git-ignored). Ask ~20 real questions in the browser, read `/stats`, note problems.
7. Go/no-go 2026-11-13: checklist from the logs and `eval/results.md` (accuracy, refusals, latency, cost per answer, crash-free, attribution visible; if public: rate limit, cost cap, GTA 6 data plan).

### Week 7 — typos in names (before the go/no-go)
Real questions: misspelled names crash the gate score ("trevers special abilty" 0.30 vs "trevor special ability" 0.58), so they're refused before search. Fix: snap near-miss words to known names before the gate and the search.
Tests: `tests/test_week7.py` (9) and `tests/test_week7_app.py` (4, gate score in the log — done 2026-11-03).
1. `title_words(chunks, ignore=(), min_len=4)` → set of lowercase letter-only words from chunk titles, at least `min_len` long, minus `ignore`.
2. `fix_typos(question, vocabulary, cutoff=0.75, min_len=4)` → the question lowercased, with every word of at least `min_len` letters that isn't in the vocabulary replaced by its closest vocabulary word (`difflib.get_close_matches`, n=1) if one is above `cutoff`; punctuation and other words kept.
3. Wire-up in `runs/serve.py` / the eval run: vocabulary = `title_words(chunks, ignore={...generic words like "store", "residence"...})` plus a few common words players misspell ("ability", "special"); run `detect_game` on the original question, then `fix_typos` before the gate, search and prompt. Log the original question.
4. Measure: `eval/golden_typos.json` (12 misspelled versions of answerable questions, `must_contain`) — score and accuracy before vs after; then the 44 set and trap set again to check nothing else broke (go/no-go Q1–Q4, Q6).

### Deploy (go/no-go P1–P4, C2) — host: Google Cloud Run (decided 2026-11-03). Hugging Face Spaces was the first choice, but Docker Spaces on free hardware need PRO since July 2026. Cloud Run: same Dockerfile, scales to zero (cold start on the first request), free tier 2M requests / 180k vCPU-s / 360k GiB-s per month, disk not persistent → the log resets when an instance stops.
1. Rate limit (P3) — done 2026-11-03 (`check_rate` 4/4, app 3/3). Spec in `tests/test_week7.py` (`check_rate`, 4) and `tests/test_week7_app.py` (3): `check_rate(times, now, limit, window=60.0)` → `(allowed, kept)`; `create_app(answer_fn, log_path, max_per_minute=10, clock=time.monotonic)` keeps a dict visitor → times; visitor = first address in `x-forwarded-for`, else `request.client.host`; over the limit → 429 `{"error": "rate_limited"}`, no model call, not logged; checked before validation.
2. Page (done by Claude 2026-11-03): privacy line, coverage line, "non-commercial", message for `rate_limited` (P4, P6).
3. Spending cap on the Anthropic API key, in the console (C2) — Itay, by hand.
4. Dockerfile + Space config (written by Claude 2026-11-03: `Dockerfile`, `.dockerignore`, `runs/build_index.py`, HOST/PORT from env in `runs/serve.py`); build `data/index.json` during the image build; `ANTHROPIC_API_KEY` from Secret Manager; uvicorn on 0.0.0.0:$PORT; `--max-instances 1`, 2 GiB memory (P1, P2).
5. Ask ~10 questions on the live URL; check `/stats`.

## Progress
- Week 1: done (21/21 passing)
- Week 2 Days 1–5 code: done — `fetch_page`, `list_category`, infobox functions, `ingest`, `chunk_stats` (plus my own `raw_to_cache` helper)
- Week 2 Day 6: done — `validate_golden` passing; `golden.json` has 31 questions over 19 of 21 pages; `golden_unanswerable.json` has 4
- All tests: 40/40 passing (Weeks 1–2); Week 3: 21/21
- Real data: 21 hand-saved gta.wiki pages in `data/raw/` → `data/cache/` → `data/chunks.json`. Fixes A (heading levels) and B (skip-list) done; Entity XF re-saved. Current stats: 687 chunks, avg 809.9 chars, 0 empty, 129 too long. Details in `notes/cleaning_notes.md`.
- Week 2 Day 7: done — baseline 0.516; + stopwords 0.677; + `?` stripping 0.774 (24/31). Misses left are mostly word mismatches. Details in `eval/results.md`.
- Week 3 Day 1 (`dot`, `norm`, `cosine_similarity`): done (6/6)
- Week 3 Day 2 (`chunk_to_embed_text`, `embed_chunks`): done (4/4)
- Week 3 Day 3 (`save_index`, `load_index`): done (3/3)
- Week 3 Day 4 (`semantic_search`, `make_semantic_search`): done (3/3)
- Week 3 Day 5 (real run, `week3_run.py`): done — semantic 0.774, ties keyword; only 2 misses shared, 5 of semantic's 7 misses are Infobox chunks; ceiling 29/31 for a hybrid. `find_misses` added to `cheatsheet.py`.
- Week 3 Day 6 (`rrf_merge`, `make_hybrid_search`): code done (5/5) — all 61 tests passing. Hybrid on real data: 0.903 (28/31) vs 0.774 for keyword and semantic alone; ceiling 0.935.
- Week 3 Day 7: done — holdout v2 (30, player words): keyword 0.500, semantic 0.767, hybrid 0.767; 14 unanswerable; candidate refusal threshold 0.55 (2/30 answerable refused, 1/14 unanswerable answered). Details in `eval/results.md`.
- Week 4 Day 1 (`format_context`, `build_prompt`): done (5/5)
- Week 4 Day 2 (`should_answer`): done (4/4)
- Week 4 Day 3 (`parse_citations`, `valid_citations`): done (4/4)
- Week 4 Day 4 (`cited_sources`): done (2/2)
- Week 4 Day 5 (`answer_question`): done (5/5) — full pipeline: gate → search → prompt → model → citation check → answer
- Week 4 Day 6 (`answer_matches`, `score_answers`): done — all 23 Week 4 tests passing
- Week 4 Day 7 (`week4_run.py`): done — 44 q, accuracy 0.75 keyword / ≈0.89 by hand, $0.0100, 1.97 s per call. Details in `eval/results.md`.
- Prompt v2 (no links, plain text): done 2026-10-28.
- Week 5 Day 0 (trap questions + baseline): done — 10 traps, 0 wrong-game answers; gate fixed with `gate_score` (max of full and `strip_game_words`).
- Week 5 path fix P1–P3: done (9/9) — chunks have `path`, index rebuilt. Trap 8/10, 44-set ≈0.89 by hand. Gate threshold re-tuned to 0.53 on the new vectors (default in `answer_question`; better passed from the run script).
- Isolate-the-stage check: the 4 gate-passing refusals (TBoGT missions, Buzzard GTA 6, Dave Norton, freighter) are all retrieval misses. Game names → game filter; Norton/freighter → vocabulary mismatch, parked (reranker / query rewrite later).
- Week 5 Day 1 (`section_games`, `infobox_games`): done (10/10).
- Week 5 Day 2 (`chunk_games`, `add_games`, `count_by_game`): done (5/5). Real data with paths: all 407, V 164, Online 124, IV 21, VI 7 (section-only reference was all 489, V 136, Online 71, IV 17). No re-embed needed: `games` isn't part of the embed text; apply `add_games` after `load_chunks`.
- Week 5 Day 3 (`matches_game`, `filter_by_game`): done (3/3).
- Week 5 Day 4 (`detect_game`): done (5/5).
- Week 5 Day 5 (`make_game_search`): done (1/1) — all Week 5 code written (37 tests).
- Week 5 real run: done 2026-11-01 — filter in `week5_run.py` (`answer_with_game`, default=None). Trap 9/10, unanswerable 14/14, 44-set ≈0.89 by hand (unchanged). Keep the filter. Zentorno Online price lost (RRF reshuffle + 'cost' vs 'price').
- Holdout #1 relabelled (GTA V / 400) and `default="V"` tested 2026-11-01: no gain over None (both 38/44 by hand). Week 5 done.
- Week 6 Day 1 (`log_entry`, `append_jsonl`, `read_jsonl`): done (7/7).
- Week 6 Day 2 (`log_summary`): done (3/3).
- Week 6 Day 3 (`validate_question`, `source_links`): done — all 15 helper tests pass.
- Week 6 Day 4 (`app.py`: `create_app`, `GET /`, `POST /ask`): done (4/4 app tests).
- Week 6 Day 5 (logging in `/ask`, 503 on model error, `GET /stats`): done — all 7 app tests (22 Week 6 tests in total).
- Week 6 Day 6: done 2026-11-02 — `runs/serve.py` (`python -m runs.serve`, http://127.0.0.1:8000), page with JS fetch to `/ask`, 36 real questions logged; findings in `eval/results.md` (name typos refused at the gate, infobox facts missed when reworded, hostile input safe).
- Week 6 Day 7: checklist written 2026-11-03 in `eval/go_no_go.md` (decision 2026-11-13). Before then: gate `score` in `log_entry`, name-typo correction + typo eval set, final re-runs, then deploy items only if it looks like a go.
- Week 7: gate score in the log done (4/4); `title_words` + `fix_typos` done (9/9). Measured 2026-11-03 (`runs/week7_run.py`, `use_fix` switch): typo set 4/12 → 12/12; trap 9/10 and 44 set 38/44 unchanged, 14/14 unanswerable refused. Keep it.
- Cleaning fixes D, C, E, G1 still open; E (split long chunks) may matter more once embeddings truncate long texts — decide from the Week 3 Day 5 misses
- Weird Gloop declined scripted access (2026-10-28). Data source for anything beyond the 21 hand-saved pages is an open decision.

Update this section when a day's tests all pass.

## Recurring slips to watch for in reviews
- String methods (`strip`, `replace`, `split`, `join`) return a new value; the result must be assigned (`x = x.strip()`).
- Newline is `"\n"` (backslash), not `"/n"`.
- Indentation: checks that belong after a loop (or inside an `if`) end up at the wrong level.
- Indexing vs slicing: `lines[i]` is one item, `lines[i:]` is a list.
- Leftover `def name(): pass` placeholders lower in the file override the real function (the later definition wins).
- `json.load(open(path))`, not `json.load(path)`.
- Strings vs ints: `"2" != 2`; convert before comparing or checking `in`.
- Reassigning the loop variable (`r = int(r)`) doesn't change the list; build a new list.
- Chunk fields: `section` = the heading name (e.g. "Infobox", "Performance"), `text` = the body, `path` = full heading path. Check `chunk["section"] == "Infobox"`, read data from `chunk["text"]`.
