# Cleaning notes — first real run

**Run:** 21 gta.wiki pages → **791 chunks** (`ingest` on hand-saved pages, 2026-10-14).
Counts below are "chunks affected out of 791". One chunk can have several problems.

## Chunks per section (`Counter(...).most_common(30)`)

| Chunks | Section name |
|---:|---|
| 166 | *(empty)* |
| 95 | `=''Grand Theft Auto V''` |
| 38 | `=Personality` |
| 26 | `Intro` |
| 26 | `=''Grand Theft Auto Online''` |
| 19 | `Background` |
| 18 | `Infobox` |
| 18 | `Navigation` |
| 17 | `Description` |
| 16 | `Design` |
| 15 | `Performance` |
| 15 | `=''Grand Theft Auto V'' and ''Online''` |
| 14 | `=Relationships` |
| 12 | `=''The Ballad of Gay Tony''` |
| 10 | `Influence` |
| 10 | `Trivia` |
| 10 | `Oversights` |
| 10 | `=Appearance` |
| 9 | `=Images` |
| 8 | `Modifications` |
| 8 | `=Design` |
| 8 | `=Traffic Default Colors` |
| 8 | `=General` |
| 7 | `=Model` / `=Population` / `=Handling` / `=Audio` (each) |
| 7 | `References` |
| 7 | `=Early Criminal Life` |
| 7 | `=''Grand Theft Auto Online'' after 2013` |

The single biggest "section" is no name at all, and 385 of 791 chunks (49%) have a name starting with `=`. Heading parsing is the first thing to fix.

---

## A. Heading bugs (`split_sections`)

| # | Problem | Chunks | Example | Cause |
|---|---|---:|---|---|
| A1 | Empty section name | 166 | `Insurgent \|  \|` | `====Vehicle====` (4-level heading): `==(.*?)==` matches with an empty middle |
| A2 | Name starts with `=` | 385 | `=Images`, `=Personality` | `===Sub===` (3-level): regex takes `==` + `=Sub` |
| A3 | Italic/bold markup in names | 166 | `=''Grand Theft Auto V''` | Heading text isn't cleaned |

**Fix direction:** count the `=` signs on both sides and take what's between them; strip `'` markup from the name. Decide whether a subsection should be named `Design` or `Design > Images` (parent + child keeps context).

## B. Whole sections that should be dropped

**101 chunks** sit in sections that will never answer a player question:
Images, Gallery, Video Gallery, Navigation, References, See Also, Traffic Default Colors, Rockstar Games Website, and the spec sub-sections (Model, Population, Handling, Audio, Language).

**Fix direction:** a skip-list of section names, checked before chunking. Cheapest big win: removes ~13% of chunks in one step.
*Note:* Handling/Model hold real facts (top speed, etc.) inside templates — skip now, parse later (see F).

## C. Markup left in the text (`clean_text`)

| # | Problem | Chunks | Example |
|---|---|---:|---|
| C1 | Wiki links `[[...]]` | 591 | `[[Nagasaki]]`, `[[Franklin Clinton\|Franklin]]` |
| C2 | Templates `{{...}}` (multi-line ones survive) | 202 | `{{Expand\|'''Minigun'''\| ... }}`, `{{Gallery ...}}` |
| C3 | Image/file lists | 158 | `Artwork-PestControl-GTAV.jpg\|...` |
| C4 | Bold/italic `'''` / `''` | 141 | `'''Buzzard Attack Chopper'''` |
| C5 | HTML tags | 50 | `<br>` |
| C6 | Category & other-language links | 22 | `[[Category:Vehicles]]`, `[[de:Der Juwel...]]` |
| C7 | Editor comments | 19 | `<!--Please ensure you have read...-->` |

**Fix direction:**
- Links: `[[target|shown]]` → `shown`; `[[target]]` → `target`; drop `[[Category:..]]`, `[[File:..]]` and `[[xx:..]]` entirely.
- Templates must be removed across newlines — the current regex stops at a line break.
- Order matters: remove comments and templates before links and bold.

## D. Missing words — templates deleted instead of replaced

**67 chunks** show gaps: `"based on the , an attack variant"`, `"conclusion of s storyline"`, `"New '''' copies"`.

**Cause:** some templates *are* text. `{{V}}` means *Grand Theft Auto V*, `{{O}}` means *GTA Online*, `{{WP|AH-64 Apache}}` shows "AH-64 Apache". Deleting them deletes words.

**Fix direction:** replace a small set of known templates with their text before removing the rest:
`{{V}}` → Grand Theft Auto V · `{{O}}` → GTA Online · `{{WP|x}}` / `{{WP|x|y}}` → the last part. Check the raw pages for other short ones.

## E. Chunk sizes (`make_chunks`)

| Problem | Chunks |
|---|---:|
| Over 1000 characters | 135 (all single paragraphs; longest 13,170) |
| Under 40 characters | 15 |

**Cause:** `make_chunks` packs *paragraphs*; one huge paragraph (often a table or template block) can't be split.
**Fix direction:** most of these disappear after B and C. For the rest, split long paragraphs on sentences or list items (`*`). Very short chunks: merge into the previous chunk or drop.

## F. Structured data (later — hardest)

| Problem | Chunks |
|---|---:|
| Wiki tables `{\| ... \|}` (Variants, Modifications) | 13 |
| Spec templates (`{{Specifications Vehicle Handling ...}}`) | in the 101 of B |

**Infobox chunks are full of markup too** (Kuruma):
`class: [[:Category:Sports class|Sports]]` · `price: [[Money|$]]126,350 {{Small|(...)}}` · `front_image: Kuruma-GTAOe-FrontQuarter.png`
**Fix direction:** run infobox values through the same link/template cleaning; drop image fields (`*_image`, `caption`, `style`).

## G. Data and collection issues (not code bugs)

1. **Pages cover several games.** Buzzard Attack Chopper has GTA IV (*The Ballad of Gay Tony*) and GTA VI sections. 13 chunks mention GTA IV/TBoGT, 7 mention GTA VI. A GTA V question could get a GTA IV answer.
   → Add a `game` field to chunks (from the section name where possible) and filter by it at search time.
2. **Character pages have no infobox chunk.** Michael, Franklin and Trevor use `{{/infobox}}` — the infobox lives on a separate sub-page, so `find_block` finds nothing (18 infobox chunks for 21 pages).
   → Save the sub-pages too (`Michael_De_Santa/infobox`) or accept it for now.
3. **Wrong title from a filename typo.** `Entity_Xf.txt` became title `Entity Xf`; the real page is `Entity XF`. Titles must match the wiki exactly (they're used for links and the golden set).
   → Rename to `Entity_XF.txt`, delete `cache/Entity_Xf.json`, rerun `raw_to_cache`.
4. **Some pages are GTA Online-only** (Insurgent, Kuruma (Armored)). Fine, but label it — players ask about story mode and Online differently.

## H. Test gaps found by the real run

- `ingest` crashed on a string `cache_dir` — tests only ever passed a `Path`. Add a test using `str(tmp_path)`.
- Tests used a clean one-line-per-field infobox and `==` headings only. Add test pages with `===`/`====` headings and multi-line templates before fixing A and C, so the fix is test-first.

---

## Suggested order

1. **A** — heading levels (49% of chunks have bad names)
2. **B** — skip-list of junk sections (−101 chunks)
3. **D** — replace text-bearing templates before deleting the rest
4. **C** — links, multi-line templates, bold, HTML, comments
5. **E** — re-measure with `chunk_stats`; split what's still too long
6. **G1** — `game` field on chunks
7. **F** — tables, spec templates, infobox cleanup

After each step: rerun `ingest`, rerun the Counter, and compare numbers with this file.

## chunk_stats (fill in after Day 5)

| Run | count | avg_chars | empty | too_long |
|---|---:|---:|---:|---:|
| First real run (2026-10-14) | 791 | | | |
