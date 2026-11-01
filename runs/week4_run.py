from cheatsheet import load_index, load_chunks, embed_chunks, make_semantic_search, save_index, keyword_search, make_hybrid_search, cosine_similarity, score_answers, answer_question
from sentence_transformers import SentenceTransformer
from pathlib import Path
import anthropic
import json
import time
from dotenv import load_dotenv
load_dotenv()

MODEL_NAME = "all-MiniLM-L6-v2"
chunks = load_chunks("data/chunks.json")
golden_holdout = json.load(open("eval/golden_holdout.json"))
model = SentenceTransformer(MODEL_NAME)
unanswerable = json.load(open("eval/golden_unanswerable.json"))
client = anthropic.Anthropic()

calls = []

def call_claude(prompt):
  start = time.perf_counter()
  response = client.messages.create(
      model="claude-haiku-5-5",
      max_tokens=1000,
      messages=[{"role": "user", "content": prompt}],
  )

  seconds = time.perf_counter() - start
  tokens_in = response.usage.input_tokens 
  tokens_out = response.usage.output_tokens 
  calls.append({"in": tokens_in, "out": tokens_out, "seconds": seconds})

  text = ""
  for block in response.content:
    if block.type == "text":
      text = block.text

  print(response.stop_reason)
  return text

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


answer_fn = lambda q: answer_question(q, chunks, hybrid, top_score, call_claude)
all_questions = golden_holdout + unanswerable

results = {}

for item in all_questions:
  result = answer_fn(item["question"])
  results[item["question"]] = result
  print("Q:", item["question"])
  print("refused: ", result["refused"])
  print("A: ", result["answer"])
  print("------")

accuracy = score_answers(all_questions, lambda q: results[q])

print("===== SUMMARY =====")
print("accuracy:", round(accuracy, 3))
print("claude calls:", len(calls), "of", len(all_questions))

if len(calls) > 0:
  total_input_tokens = sum(call["in"] for call in calls)
  total_output_tokens = sum(call["out"] for call in calls)
  cost = ((total_input_tokens / 1000000) * 0.1) + ((total_output_tokens / 1000000) * 0.5)
  avg_latency = sum(call["seconds"] for call in calls) / len(calls)

  print("tokens in:", total_input_tokens)
  print("tokens out:", total_output_tokens)
  print("cost: $", round(cost, 5))
  print("avg latency:", round(avg_latency, 2), "s")
else:
  print("no Claude calls made")