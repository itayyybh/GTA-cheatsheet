from cheatsheet import load_index, load_chunks, embed_chunks, make_semantic_search, save_index, recall_at_k, keyword_search, find_misses, make_hybrid_search, cosine_similarity
from sentence_transformers import SentenceTransformer
from pathlib import Path
import json

MODEL_NAME = "all-MiniLM-L6-v2"
chunks = load_chunks("data/chunks.json")
golden = json.load(open("eval/golden.json"))
golden_holdout = json.load(open("eval/golden_holdout.json"))
model = SentenceTransformer(MODEL_NAME)
unanswerable = json.load(open("eval/golden_unanswerable.json"))

path = Path("data/index.json")
if path.exists():
  chunks, vectors = load_index(path, MODEL_NAME)
else:
  vectors = embed_chunks(chunks, model.encode, batch_size=32)
  save_index(path, MODEL_NAME, chunks, vectors)

semantic = make_semantic_search(vectors, model.encode)
hybrid = make_hybrid_search([keyword_search, semantic])

def top_score(question):
  vector_list = model.encode([question])
  query_vector = vector_list[0]
  return max(cosine_similarity(query_vector, v) for v in vectors)

# keyword_search_result = recall_at_k(keyword_search, golden, chunks, k=5)
# semantic_result = recall_at_k(semantic, golden, chunks, k=5)
# hybrid_result = recall_at_k(hybrid, golden, chunks, k=5)

top_holdout = [float(top_score(item["question"])) for item in golden_holdout]
top_unanswerable = [float(top_score(item["question"])) for item in unanswerable]

print("answerable:  ", sorted(top_holdout))
print("unanswerable:  ", sorted(top_unanswerable))

# keyword_search_result = recall_at_k(keyword_search, golden_holdout, chunks, k=5)
# semantic_result = recall_at_k(semantic, golden_holdout, chunks, k=5)
# hybrid_result = recall_at_k(hybrid, golden_holdout, chunks, k=5)

# print("keyword_search result:", keyword_search_result)
# print("semantic result:", semantic_result)
# print("hybrid result: ", hybrid_result)

# # keyword_search_misses = find_misses(keyword_search, golden_holdout, chunks)
# semantic_misses = find_misses(semantic, golden_holdout, chunks)
# hybrid_misses = find_misses(hybrid, golden_holdout, chunks)

# # print("missed by both: ", set(keyword_search_misses) & set(semantic_misses))
# print("missed only by hybrid: \n", set(hybrid_misses) - set(semantic_misses))
# print("missed only by semantic: \n", set(semantic_misses) - set(hybrid_misses))
# print("missed by both: \n", set(hybrid_misses) & set(semantic_misses))
# print(len(vectors))





