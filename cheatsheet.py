import re
import json
import requests
import time
from pathlib import Path
import math
import difflib

SKIP_SECTIONS = {
    "Images", "Gallery", "Video Gallery", "Navigation", "References",
    "See Also", "Traffic Default Colors", "Rockstar Games Website",
    "Model", "Population", "Handling", "Audio", "Language",
}

STOPWORDS = {
    'i', 'a', 'an', 'the', 'is', 'are', 'do', 'does', 'how',
    'what', 'which', 'who', 'where', 'when', 'can',
    'in', 'on', 'of', 'to', 'for',
    'and', 'my', 'me', 'you', 'it', 'get', 'much',
    }

#cleans text from unwanted symbols from WikiText
def clean_text(text):
    text = text.replace("[edit]", "")
    text = re.sub(r"\{\{.*?\}\}", "", text)
    text = re.sub(r" +", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    return text


# Split cleaned wikitext into [{heading, text}] sections at == headings (Intro for the text before the first one).
def split_sections(text):
    result = []
    current_heading = "Intro"
    current_lines = []

    for line in text.splitlines():
        line = line.strip()
        if line.startswith('=') and line.endswith('='):
            header = line
            header = header.strip('=').replace("'", "").strip()
            section_text = "\n".join(current_lines).strip()

            if section_text:
                result.append({"heading": current_heading, "text": section_text})

            current_heading = header
            current_lines = []

        else:
            current_lines.append(line)

    section_text = "\n".join(current_lines).strip()

    if section_text:
        result.append({"heading": current_heading, "text": section_text})

    return result

# Count the leading '=' of a heading line (== Name == -> 2); 0 if the line isn't a heading.
def heading_level(line):
    if line.startswith('=') and line.endswith('='):
        return line.count('=') // 2
    return 0 

# Like split_sections, but each section also gets a path of its parent headings ("Locations > Grand Theft Auto Online").
def split_sections_with_path(text):
    result = []
    current_heading = "Intro"
    stack = []
    path = "Intro"
    current_lines = []

    for line in text.splitlines():
        line = line.strip()
        if line.startswith('=') and line.endswith('='):
            header = line
            header = header.strip('=').replace("'", "").strip()
            section_text = "\n".join(current_lines).strip()

            if section_text:
                result.append({"heading": current_heading, "path": path, "text": section_text})

            level = heading_level(line)
            stack = [pair for pair in stack if pair[0] < level]
            stack.append((level, header))
            path = " > ".join(pair[1] for pair in stack)
            current_heading = header
            current_lines = []

        else:
            current_lines.append(line)

    section_text = "\n".join(current_lines).strip()

    if section_text:
        result.append({"heading": current_heading,"path": path, "text": section_text})

    return result

# Turn one page into chunks {title, url, section, text}, skipping junk sections and splitting text longer than max_chars.
def make_chunks(page, max_chars=1000):

    chunks = []

    for item in split_sections(page["text"]):
        if item["heading"] in SKIP_SECTIONS:
            continue
        paragraph = item["text"].split("\n\n")
        current = ""

        for para in paragraph:
            if len(current) == 0:
                current = para

            elif len(current) + 2 + len(para) <= max_chars:
                current = current + "\n\n" + para

            else:
                chunks.append(
                    {
                        "title": page["title"],
                        "url": page["url"],
                        "section": item["heading"],
                        "text": current,
                    }
                )
                current = para

        chunks.append(
            {
                "title": page["title"],
                "url": page["url"],
                "section": item["heading"],
                "text": current,
            }
        )

    return chunks

# Same chunks as make_chunks, plus a path field with the full heading path.
def make_path_chunks(page, max_chars=1000):
    chunks = []

    for item in split_sections_with_path(page["text"]):
        if item["heading"] in SKIP_SECTIONS:
            continue
        paragraph = item["text"].split("\n\n")
        current = ""

        for para in paragraph:
            if len(current) == 0:
                current = para

            elif len(current) + 2 + len(para) <= max_chars:
                current = current + "\n\n" + para

            else:
                chunks.append(
                    {
                        "title": page["title"],
                        "url": page["url"],
                        "section": item["heading"],
                        "path": item["path"],
                        "text": current,
                    }
                )
                current = para

        chunks.append(
            {
                "title": page["title"],
                "url": page["url"],
                "section": item["heading"],
                "path": item["path"],
                "text": current,
            }
        )

    return chunks




# Write a list of chunks to a JSON file.
def save_chunks(chunks, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)


# Read a list of chunks back from a JSON file.
def load_chunks(path):
    with open(path, "r", encoding="utf-8") as f:
        result = json.load(f)

        return result

# Convert hand-saved raw wikitext files into cached page dicts {title, url, text}.
def raw_to_cache(raw_dir, cache_dir, base_url):

    titles = []

    cache_dir = Path(cache_dir)
    cache_dir.mkdir(exist_ok=True)

    for filename in Path(raw_dir).glob("*.txt"):
        name  = filename.stem
        title = name.replace("_", " ")
        url = base_url + '/w/' + name
        with open(filename, encoding="utf-8") as f:
            text = f.read()
        page = {"title": title, "url": url, "text": text}
        path = cache_dir / (name + ".json")

        save_chunks(page, path)
        titles.append(title)

    return titles



# Turn a MediaWiki parse API response into a page dict {title, url, text}.
def parse_api_response(data, base_url):
    parse = data["parse"]
    url = base_url + "/wiki/" + parse["title"].replace(" ", "_")
    return {"title": parse["title"], "url": url, "text": parse["wikitext"]}


# Download one page's wikitext from the MediaWiki API (get is injected so tests use a fake).
def fetch_page(title, base_url, get=requests.get):

    response = get(
        base_url + "/api.php",
        params={
            "action": "parse",
            "page": title,
            "prop": "wikitext",
            "format": "json",
            "formatversion": "2",
        },
        headers = {"User-Agent": 'GTA_Cheatsheet'},
        timeout = 10
    )

    response.raise_for_status()
    data = response.json()

    return parse_api_response(data, base_url)

# List all article titles in a wiki category, following the API's continue pages.
def list_category(category, base_url, get=requests.get):
    params = {'action': "query",
            'list': "categorymembers",
            'cmtitle': 'Category:' + category,
            'cmlimit': 500,
            'format': 'json',
            'formatversion': '2'}
    titles = []

    while True:
        response = get(base_url + '/api.php', params=params, headers={"User-Agent": 'GTA_Cheatsheet'})
        response.raise_for_status()

        data = response.json()

        for i in data["query"]["categorymembers"]:
            if i["ns"] == 0:
                titles.append(i["title"])

        if "continue" in data: 
            params["cmcontinue"] = data["continue"]["cmcontinue"]
        else:
            return titles


# Find where the infobox starts and ends in a list of lines; returns the (start, end) indexes or None.
def find_block(lines):

    start = None
    end = None
    
    for i, line in enumerate(lines):
        
        if line.strip().startswith('{{Infobox'):
            start = i
            break
        
    if start is None:
        return None

    for i in range(start, len(lines)):
        
        if lines[i].strip() == '}}':
            end  = i
            break
        
    if end is None:
        return None 

    return start, end

# Read the infobox at the top of a page into {type, fields}; None if there is no infobox.
def parse_infobox(wikitext):
    lines = wikitext.split('\n')
    results = find_block(lines)

    if results is None:
        return None
    
    start, end = results
    box_type = lines[start].replace('{{Infobox', '').strip()

    fields = {}
    for line in lines[start +1: end]:
        line = line.strip()
        if line.startswith('|') and '=' in line:
            line = line[1:]
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            if value: 
                fields[key] = value
    return {"type": box_type, "fields": fields}

# Make one Infobox chunk with 'key: value' lines from a page's infobox; None if there is none.
def infobox_to_chunk(page):
    chunk = {}
    parse = parse_infobox(page["text"])
    if parse is None:
        return None

    chunk["title"] = page["title"]
    chunk["url"] = page["url"]
    chunk["section"] = "Infobox"

    items = []

    for key, value in parse["fields"].items():
        items.append(f"{key}: {value}")

    text = "\n".join(items)

    chunk["text"] = text
    return chunk


# Return the wikitext without its infobox lines.
def remove_infobox(wikitext):
    lines = wikitext.split('\n')
    results = find_block(lines)

    if results is None:
        return wikitext

    start, end = results
    lines = lines[:start] + lines[end+1:]
    text = "\n".join(lines).strip()

    return text

# Load each page from the cache (or fetch and save it), then return all its chunks: infobox chunk first, then sections.
def ingest(titles, base_url, cache_dir, get=requests.get, sleep=time.sleep, delay=1.0):
    
    chunks = []
    cache_dir = Path(cache_dir)
    for title in titles:
        
        name = title.replace(' ', '_')
        filename = name + '.json'
        path = cache_dir / filename

        if path.exists():
            page = load_chunks(path)
        else:
            page = fetch_page(title, base_url, get=get)
            save_chunks(page, path)
            sleep(delay)

        infobox_chunk = infobox_to_chunk(page) 
        if infobox_chunk:
            chunks.append(infobox_chunk)   

        text = remove_infobox(page["text"])
        clean = clean_text(text)

        result = make_path_chunks({**page, "text": clean})
        chunks += result

    return chunks


# Score chunks by how many question words (minus stopwords) they contain; return the top k.
def keyword_search(chunks, query, k):

    results = []

    words = set(query.lower().split())
    words = {word.strip("?") for word in words} - STOPWORDS

    for chunk in chunks:
        haystack = " ".join([chunk["title"], chunk["section"], chunk["text"]]).lower()

        score = 0
        for word in words:
            if word in haystack:
                score += 1

        if score > 0:
            results.append((score, chunk))

    sorted_result = sorted(results, key=lambda pair: pair[0], reverse=True)
    final_result = sorted_result[:k]

    final_result_list = []
    for result in final_result:
        final_result_list.append(result[1])

    return final_result_list


# Share of golden questions whose expected chunk (title + section) is in the search's top k.
def recall_at_k(search_fn, golden, chunks, k):
    hits = 0

    for item in golden:
        search_result = search_fn(chunks, item["question"], k)

        for i in search_result:
            if (
                i["section"] == item["expected_section"]
                and i["title"] == item["expected_title"]
            ):
                hits += 1
                break

    if len(golden) > 0:
        return hits / len(golden)

    else:
        return 0.0

# List the golden questions whose expected chunk is not in the top 5 results.
def find_misses(search_fn, golden, chunks):
    misses_questions = []
    for item in golden:
        results = search_fn(chunks, item["question"], 5)

        found = any(r["title"] == item["expected_title"] and r["section"] == item["expected_section"] for r in results)

        if not found: 
            misses_questions.append(item["question"])
        
    return misses_questions
    


# Count, average length, empty and too-long chunks, to measure cleaning.
def chunk_stats(chunks, max_chars=1000):
    count = len(chunks)
    too_long = 0
    empty = 0
    total = 0
    if count == 0:
        return {"count": count, "too_long": too_long, "empty": empty, "avg_chars": 0.0}
    
    for chunk in chunks:
        if not chunk["text"].strip():
            empty += 1
        if len(chunk["text"]) > max_chars:
            too_long += 1
        total += len(chunk["text"])
    avg_chars = round(total / count, 1)

    c = {"count": count, "too_long": too_long, "empty": empty, "avg_chars": avg_chars}

    return c

# Check golden items for missing keys, empty and duplicate questions; returns (index, problem) pairs.
def validate_golden(items):
    problems = []
    seen = set()

    for index, item in enumerate(items):
        if "question" not in item or "expected_title" not in item or "expected_section" not in item:
            problems.append((index, "missing_key"))
            continue
        q = item["question"].lower().strip()
        if not q:
            problems.append((index, "empty_question"))
        elif q in seen:
            problems.append((index, "duplicate_question"))
        else:
            seen.add(q)
    return problems

# Dot product of two vectors.
def dot(a, b):
    total = 0
    for i in zip(a, b):
         total += i[0] * i[1]
    return total

# Length (magnitude) of a vector.
def norm(a): 
    return math.sqrt(dot(a, a))

# How similar two vectors point, from -1 to 1 (0 if either has zero length).
def cosine_similarity(a, b):
    if norm(a) == 0 or norm(b) == 0:
        return 0.0
    return dot(a, b) / (norm(a) * norm(b))

# The chunk's heading path if it has one, else its section name.
def chunk_label(chunk):
    return chunk.get("path", chunk["section"])

# The text that gets embedded for a chunk: 'title | label' then the chunk text.
def chunk_to_embed_text(chunk): 
    return f"{chunk['title']} | {chunk_label(chunk)}\n{chunk['text']}"

# Embed all chunks in batches with embed_fn; returns one vector per chunk, same order.
def embed_chunks(chunks, embed_fn, batch_size=32):
    results = []
    texts = [chunk_to_embed_text(chunk) for chunk in chunks]
    batches = range(0, len(texts), batch_size)

    for start in batches:
        vectors = embed_fn(texts[start:start + batch_size])
        results.extend([[float(number)for number in x] for x in vectors])
    return results
            

# Save the model name, chunks and vectors to one JSON index file.
def save_index(path, model, chunks, vectors):
    if len(chunks) != len(vectors):
        raise ValueError("chunks and vectors are not the same length")
    data = {"model": model, "chunks": chunks, "vectors": vectors}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# Load chunks and vectors from the index; error if it was built with a different model.
def load_index(path, model): 
    with open(path, "r", encoding="utf-8") as f:
        result = json.load(f)
        if result["model"] != model:
            raise ValueError("the saved 'model' isn't the model argument")
        return result["chunks"], result["vectors"]

# Rank chunks by cosine similarity between their vectors and the query vector; return the top k.
def semantic_search(chunks, vectors, query_vector, k):
    results = []
    for chunk, vector in zip(chunks, vectors):
        score = cosine_similarity(vector, query_vector)
        results.append((score, chunk))
    results.sort(reverse=True, key=lambda pair: pair[0])
    top_pair = results[:k]
    return [p[1] for p in top_pair]


# Build a search(chunks, query, k) that embeds the query and runs semantic_search over the given vectors.
def make_semantic_search(vectors, embed_fn): 
    def search(chunks, query, k):
        vector_list = embed_fn([query])
        query_vector = vector_list[0]
        return semantic_search(chunks, vectors, query_vector, k)
    return search
    

# Merge several ranked lists with Reciprocal Rank Fusion (1 / (c + rank) per list); return the top k.
def rrf_merge(result_lists, k, c=60): 
    scores = {}
    chunk_by_key = {}
    for results in result_lists:
        for rank, chunk in enumerate(results, start=1):
            key = (chunk["title"], chunk["section"], chunk["text"])
            scores[key]= scores.get(key, 0) + 1 / (c + rank)
            chunk_by_key[key] = chunk
    ranked_keys = sorted(scores, key=lambda t: scores[t], reverse=True)[:k]
    return [chunk_by_key[key] for key in ranked_keys]


# Build a search that runs every search function with a pool and merges them with RRF.
def make_hybrid_search(search_fns, pool=20): 
    def search(chunks, query, k):
        results = [f(chunks, query, pool) for f in search_fns]
        return rrf_merge(results, k)
    return search

# Number the chunks as sources for the prompt: '[1] title | label' then the text.
def format_context(chunks):
    result = []
    for index, chunk in enumerate(chunks, start=1):
        block = (f'[{index}] {chunk["title"]} | {chunk_label(chunk)}\n{chunk["text"]}') 
        result.append(block)
    result_string = "\n\n".join(result)
    return result_string

# Build the Claude prompt: instructions, numbered sources, then the question last.
def build_prompt(question, chunks):
    instructions = "answer questions from users about GTA using only the source below," \
    " cite the source number like [1], [2]." \
    " if it is not in the source reply exactly NOT_DOCUMENTED." \
    " keep answers short." \
    " answer in players tone." \
    " Do not include any links or URLs." \
    " use plain text no markdown formatting "
    source = format_context(chunks)
    q = f"Question:  {question}"
    result = [instructions, source, q]
    result_string = "\n\n".join(result)
    return result_string

# Refusal gate: True if the retrieval score reaches the threshold.
def should_answer(score, threshold=0.55):
    return score >= threshold

# Find the [n] citation numbers in a reply, in first-seen order, without repeats.
def parse_citations(text):
    numbers = []
    result = re.findall((r'\[(\d+)\]'), text)
    for r in result:
        if int(r) not in numbers:
            numbers.append(int(r))
    return numbers

# Keep only citation numbers that point to a real source (1..n_sources).
def valid_citations(cited, n_sources):
    return [x for x in cited if 1<=x<=n_sources]

# Turn citation numbers into source dicts {n, title, section, url}.
def cited_sources(cited, chunks):
    res_list = []
    for n in cited:
        chunk = chunks[n-1]
        result = {"n": n, "title": chunk["title"], "section": chunk["section"], "url": chunk["url"]}
        res_list.append(result)
    return res_list

# Full pipeline: gate -> search -> prompt -> model -> citation check; returns {answer, sources, refused}.
def answer_question(question, chunks, search_fn, score_fn, llm_fn, k=5, threshold=0.53):
    score = score_fn(question)
    refuse = {"answer": "Not documented yet.", "sources": [], "refused": True}
    if not should_answer(score, threshold):
        return refuse
    top_chunks = search_fn(chunks, question, k)
    prompt = build_prompt(question, top_chunks)
    reply = llm_fn(prompt)
    if "NOT_DOCUMENTED" in reply:
        return refuse
    else:
        cited = parse_citations(reply)
        valid = valid_citations(cited, len(top_chunks))
    if not valid:
        return refuse
    return {"answer": reply.strip(), "sources": cited_sources(valid, top_chunks), "refused": False}

# True if the answer contains every required phrase (case-insensitive).
def answer_matches(answer, must_contain):
    return all(x.lower() in answer.lower() for x in must_contain )

# Share of golden questions whose answer contains its must_contain phrases (unanswerable ones must be refused).
def score_answers(golden, answer_fn):
    counter = 0
    for item in golden:
        result = answer_fn(item["question"])
        unanswerable = item.get("unanswerable")
        if unanswerable and result["refused"]:
            counter += 1
        elif not unanswerable and not result["refused"] and answer_matches(result["answer"], item["must_contain"]):
            counter += 1
    if len(golden) > 0:
        return counter / len(golden)


# Remove game names ('in gta online', 'tbogt', ...) from a question, for the gate score.
def strip_game_words(question):
    game_words = ["gta online", "gtao", "gta v",
                "gta 5", "gta iv", "gta vi",
                "gta 6", "story mode",
                "tbogt", "the ballad of gay tony"
                ]
    for word in game_words:
        question = re.sub(rf"(?:\bin\s+)?\b{word}\b", "", question)
        question = re.sub(r"\s+", " ", question)
    return question.strip()


# Game codes named in a heading (IV, V, Online, VI), matching whole words so VI isn't V.
def section_games(section):
    codes = ["IV", "V", "Online", "VI"]
    games = []
    words = re.findall(r"\w+", section)

    for code in codes:
        if code in words:
            games.append(code)

    if "tbogt" in section.lower() or "the ballad of gay tony".lower() in section.lower():
        games.append("IV")

    return games

# Game codes from the infobox 'games:' line (TBOGT/TLAD/IV -> IV, O -> Online).
def infobox_games(text):
    games = []
    for line in text.splitlines():
        keys = re.findall(r"\|(\w+)=", line)
        if "games:" in line:
            if "TBOGT" in keys or "TLAD" in keys or "IV" in keys:
                games.append("IV")
            if "V" in keys:
                games.append("V")
            if "O" in keys:
                games.append("Online")
            if "VI" in keys:
                games.append("VI")
    return games

# A chunk's games: from the infobox for Infobox chunks, else from its heading path; ['all'] if no clue.
def chunk_games(chunk):
    if chunk["section"] == "Infobox":
        games = infobox_games(chunk["text"])
    else:
        games =  section_games(chunk_label(chunk))
    if len(games) == 0:
        games = ["all"]
    return games

# Return copies of the chunks with a games field added; the input stays unchanged.
def add_games(chunks):
    return [{**chunk, "games": chunk_games(chunk)} for chunk in chunks]

# How many chunks belong to each game (a chunk counts once per game).
def count_by_game(chunks):
    count = {}
    for chunk in chunks:
        for game in chunk["games"]:
            count[game] = count.get(game, 0) + 1
    return count

# True if the chunk is about that game or applies to all games.
def matches_game(chunk, game):
    return game in chunk["games"] or "all" in chunk["games"]

# Keep only that game's chunks and their vectors, still paired; None keeps everything.
def filter_by_game(chunks, vectors, game):
    if game is None:
        return chunks, vectors
    chunk_list = []
    vector_list = []
    for chunk, vector in zip(chunks, vectors):
        if matches_game(chunk, game):
            chunk_list.append(chunk)
            vector_list.append(vector)
    return chunk_list, vector_list

# Which game a question names (gta 6 -> VI, tbogt -> IV, ...), or default if none.
def detect_game(question, default="V"):
    question = question.lower()
    phrases = {"Online": ["gta online", "gtao"], "VI": ["gta 6", "gta vi"], "V": ["gta v", "gta 5", "story mode"], "IV": ["gta 4", "tbogt", "gta iv", "gay tony"]}
    for game, game_phrase_list in phrases.items():
        for phrase in game_phrase_list:
            if re.search(rf"\b{phrase}\b", question):
                return game
    return default

# Filter to one game, then build a hybrid search over only those chunks; returns (game_chunks, search).
def make_game_search(chunks, vectors, game, embed_fn, pool=20):
    game_chunks, game_vectors = filter_by_game(chunks, vectors, game)
    semantic = make_semantic_search(game_vectors, embed_fn)
    hybrid = make_hybrid_search([keyword_search, semantic], pool)
    return game_chunks, hybrid

# One log record for an answered question: time, question, game, refused, answer, source urls, seconds, error.
def log_entry(question, result, game, seconds, when, error=None):
    return {"time": when, "question": question, "game": game, "refused": result["refused"], "answer": result["answer"], "sources": [n["url"] for n in result["sources"]], "seconds": round(seconds, 2), "error": error}

# Append one entry to a JSONL log file (one JSON object per line), creating the folder if needed.
def append_jsonl(path, entry):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# Read a JSONL file back into a list of dicts; [] if the file doesn't exist.
def read_jsonl(path):
    result = []
    if not Path(path).exists():
        return []
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    for line in lines:
        if line.strip():
            result.append(json.loads(line))
    return result


# Totals for the log: count, refusals, refusal rate, errors, average seconds, questions per game.
def log_summary(entries):
    count = len(entries)
    if count == 0:
        return {"count": 0, "refused": 0, "refusal_rate": 0.0, "errors": 0, "avg_seconds": 0.0, "by_game": {}}
    refused = sum(entry["refused"] for entry in entries)
    errors = len([entry["error"] for entry in entries if entry["error"] is not None])
    avg_seconds = sum(entry["seconds"] for entry in entries) / count
    by_game = {}
    for entry in entries:
        game = entry["game"] or "none"
        by_game[game] = by_game.get(game, 0) + 1
    return {"count": count, "refused": refused, "refusal_rate": round(refused / count, 3), "errors": errors, "avg_seconds": round(avg_seconds, 2), "by_game": by_game}

def validate_question(text, max_chars=300):
    text = text.strip()
    if not text:
        return (None, "empty")
    elif len(text) > max_chars:
        return (None, "too_long")
    else:
        return (text, None)

def source_links(sources):
    result = []
    seen_urls = set()
    for source in sources:
        if source["url"] not in seen_urls:
            seen_urls.add(source["url"])
            result.append({"title": source["title"], "url": source["url"]})
    return result

def title_words(chunks, ignore=(), min_len=4):
    names = set()
    for chunk in chunks:
        title = re.findall(r"[a-z]+", chunk["title"].lower())
        for t in title:
            if len(t) >= min_len and t not in ignore:
                names.add(t)
    return names


def fix_typos(question, vocabulary, cutoff=0.75, min_len=4):
    def fix_word(match):
        word = match.group(0)
        if len(word) < min_len or word in vocabulary:
            return word
        else:
            matches = difflib.get_close_matches(word, vocabulary, n=1, cutoff=cutoff)
            if not matches:
                return word
            else:
                return matches[0]
    return re.sub(r"[a-z]+", fix_word, question.lower())
