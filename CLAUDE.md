I'm relearning Python. Never write or edit code in cheatsheet.py. Only give hints, review my code, and run the tests.

# Python Refresher — GTA Cheatsheet

## Who I am and how to help
- I knew Python well years ago and am relearning it; this is recall, not starting from zero.
- I write every line of `cheatsheet.py` myself. Never write, edit or paste a solution for it, even if I'm stuck.
- When I'm stuck, give the smallest hint that unblocks me: point at the line, name the concept or method, show a tiny example on unrelated data. Not the fix.
- Reviews: list bugs most important first, say why each one fails, and what to look up. Mention what's already right.
- Keep answers short and in English.
- You may run tests: `pytest test_week2.py -k <function_name>` for one exercise, `pytest` for everything. Explain failures by reading the assertion (left side = my output, right side = expected).
- Never change the test files.

## The project
A GTA "AI cheatsheet": a RAG question-answering system over wiki pages. GTA V data now, GTA 6 data after its launch on November 19, 2026.

- `test_cheatsheet.py` — Week 1 spec (21 tests)
- `test_week2.py` — Week 2 spec (19 tests). Uses fakes for `get` and `sleep`, so no test touches the internet.
- `cheatsheet.py` — my code
- Week 1 plan: https://claude.ai/code/artifact/c2bf4f46-e812-410c-a096-992d9e9b3cf8
- Week 2 plan: https://claude.ai/code/artifact/b8402308-5372-472d-81cf-a6b6b3b1877c
- Architecture: https://claude.ai/code/artifact/826846de-0508-4d53-be1a-1eee1a5e837f

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

## Progress
- Week 1: done (21/21 passing)
- Week 2 Day 1 `fetch_page`: done (3/3 passing)
- Week 2 Day 2 `list_category`: done (3/3 passing)
- Week 2 Day 3 infobox functions: done (6/6 passing) — `find_block` helper, `parse_infobox`, `remove_infobox`, `infobox_to_chunk`
- Week 2 Day 4 `ingest`: done (3/3 passing)
- Week 2 overall: 15/19 passing; Week 1 still 21/21
- Day 4 real run still to do: hand-save ~20 GTA V pages as page dicts in a cache folder, run `ingest` on their titles, `save_chunks` the result
- Week 2 Day 5 `chunk_stats(chunks, max_chars=1000)`: next. Delete its placeholder first.
- Open: ask Weird Gloop (gta.wiki) for consent to run a slow API script for a learning project; meanwhile hand-save pages.

Update this section when a day's tests all pass.

## Recurring slips to watch for in reviews
- String methods (`strip`, `replace`, `split`, `join`) return a new value; the result must be assigned (`x = x.strip()`).
- Newline is `"\n"` (backslash), not `"/n"`.
- Indentation: checks that belong after a loop (or inside an `if`) end up at the wrong level.
- Indexing vs slicing: `lines[i]` is one item, `lines[i:]` is a list.
- Leftover `def name(): pass` placeholders lower in the file override the real function (the later definition wins).
