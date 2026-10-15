import re
import json
import requests
import time
from pathlib import Path

SKIP_SECTIONS = {
    "Images", "Gallery", "Video Gallery", "Navigation", "References",
    "See Also", "Traffic Default Colors", "Rockstar Games Website",
    "Model", "Population", "Handling", "Audio", "Language",
}

def clean_text(text):
    text = text.replace("[edit]", "")
    text = re.sub(r"\{\{.*?\}\}", "", text)
    text = re.sub(r" +", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    return text


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


def save_chunks(chunks, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)


def load_chunks(path):
    with open(path, "r", encoding="utf-8") as f:
        result = json.load(f)

        return result

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



def parse_api_response(data, base_url):
    parse = data["parse"]
    url = base_url + "/wiki/" + parse["title"].replace(" ", "_")
    return {"title": parse["title"], "url": url, "text": parse["wikitext"]}


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


def remove_infobox(wikitext):
    lines = wikitext.split('\n')
    results = find_block(lines)

    if results is None:
        return wikitext

    start, end = results
    lines = lines[:start] + lines[end+1:]
    text = "\n".join(lines).strip()

    return text

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

        result = make_chunks({**page, "text": clean})
        chunks += result

    return chunks


def keyword_search(chunks, query, k):

    results = []
    words = set(query.lower().split())

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


def validate_golden(): pass
