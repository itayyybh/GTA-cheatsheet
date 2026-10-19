from cheatsheet import load_index, load_chunks, embed_chunks, make_semantic_search, save_index, recall_at_k, keyword_search, find_misses, make_hybrid_search
from sentence_transformers import SentenceTransformer
from pathlib import Path
import json

chunks = load_chunks("data/chunks.json")
golden = json.load(open("eval/golden.json"))
MODEL_NAME = "all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)

path = Path("data/index.json")
if path.exists():
  chunks, vectors = load_index(path, MODEL_NAME)
else:
  vectors = embed_chunks(chunks, model.encode, batch_size=32)
  save_index(path, MODEL_NAME, chunks, vectors)

semantic = make_semantic_search(vectors, model.encode)
hybrid = make_hybrid_search([keyword_search, semantic])

keyword_search_result = recall_at_k(keyword_search, golden, chunks, k=5)
semantic_result = recall_at_k(semantic, golden, chunks, k=5)
hybrid_result = recall_at_k(hybrid, golden, chunks, k=5)

print("keyword_search result:", keyword_search_result)
print("semantic result:", semantic_result)
print("hybrid result: ", hybrid_result)

keyword_search_misses = find_misses(keyword_search, golden, chunks)
semantic_misses = find_misses(semantic, golden, chunks)
hybrid_misses = find_misses(hybrid, golden, chunks)

# print("missed by both: ", set(keyword_search_misses) & set(semantic_misses))
# print("missed only by keyword_search: ", set(keyword_search_misses) - set(semantic_misses))
# print("missed only by semantic: ", set(semantic_misses) - set(keyword_search_misses))
print("missed by hybrid: ", set(hybrid_misses))
print(len(vectors))





