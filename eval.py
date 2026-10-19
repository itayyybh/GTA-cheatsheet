from cheatsheet import load_chunks, keyword_search
import json

chunks = load_chunks("chunks.json")
golden = json.load(open("golden.json"))

misses = 0

for item in golden:
  results = keyword_search(chunks, item["question"], 5)

  found = any(r["title"] == item["expected_title"] and r["section"] == item["expected_section"] for r in results)

  if not found:
    misses += 1
    print("MISS:", item["question"])
    print(" expected:", item["expected_title"], "|", item["expected_section"])
    print(" got:")
    for i, r in enumerate(results[:3], start=1):
      print(f"    {i}. {r['title']} | {r['section']}")

print("misses:", misses)

