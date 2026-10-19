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
- Architecture: https://claude.ai/code/artifact/826846de-0508-4d53-be1a-1eee1a5e837f

## Folder layout
- `cheatsheet.py` — my code (tests import it from the root)
- `week3_run.py` — real-data script; run from the project root
- `tests/` — the spec files (never edit); `pytest.ini` sets `pythonpath = .` so they find `cheatsheet.py`
- `data/` — `raw/` (hand-saved wikitext) → `cache/` (page dicts) → `chunks.json`; `index.json` = embeddings, git-ignored, delete it to rebuild
- `eval/` — `golden.json`, `golden_unanswerable.json`, `results.md` (every score, dated)
- `notes/` — `cleaning_notes.md`, `LEARN.md` (💡 Learn glossary)

## Data source rules
- Do NOT use Fandom (gta.fandom.com): its terms ban automated access, and the GTA Wiki community left it for gta.wiki in March 2026.
- gta.wiki (main GTA Wiki, ~24k articles): text is CC BY-NC-SA 3.0 (attribution, non-commercial, share-alike). Its host Weird Gloop's terms forbid automated use without prior consent, so no script hits it until I have their OK.
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
- Week 3 Day 7 (no tests): next — `eval/golden_holdout.json` with 10 new questions written without looking at results; score all three methods; compare top semantic score for answerable vs unanswerable questions
- Cleaning fixes D, C, E, G1 still open; E (split long chunks) may matter more once embeddings truncate long texts — decide from the Week 3 Day 5 misses
- Open: send the Weird Gloop consent email (draft in Gmail); add `cache/` and `chunks.json` to `.gitignore`

Update this section when a day's tests all pass.

## Recurring slips to watch for in reviews
- String methods (`strip`, `replace`, `split`, `join`) return a new value; the result must be assigned (`x = x.strip()`).
- Newline is `"\n"` (backslash), not `"/n"`.
- Indentation: checks that belong after a loop (or inside an `if`) end up at the wrong level.
- Indexing vs slicing: `lines[i]` is one item, `lines[i:]` is a list.
- Leftover `def name(): pass` placeholders lower in the file override the real function (the later definition wins).

