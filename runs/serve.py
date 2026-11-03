from cheatsheet import load_index, load_chunks, embed_chunks, make_semantic_search, save_index, keyword_search, make_hybrid_search, cosine_similarity, score_answers, answer_question, strip_game_words, chunk_label, add_games, count_by_game, detect_game, make_game_search, title_words, fix_typos
from sentence_transformers import SentenceTransformer
from pathlib import Path
import anthropic
import json
import os
import time
from dotenv import load_dotenv
load_dotenv()

MODEL_NAME = "all-MiniLM-L6-v2"
chunks = load_chunks("data/chunks.json")
model = SentenceTransformer(MODEL_NAME)
client = anthropic.Anthropic()

calls = []

def call_claude(prompt):
  response = client.messages.create(
      model="claude-haiku-5-5",
      max_tokens=1000,
      messages=[{"role": "user", "content": prompt}],
  )

  text = ""
  for block in response.content:
    if block.type == "text":
      text = block.text

  return text

path = Path("data/index.json")
if path.exists():
  chunks, vectors = load_index(path, MODEL_NAME)
else:
  vectors = embed_chunks(chunks, model.encode, batch_size=32)
  save_index(path, MODEL_NAME, chunks, vectors)

chunks = add_games(chunks)
vocabulary = title_words(chunks, ignore={"store"} ) | {"ability", "special", "story", "online", "mode", "price", "speed", "missions"}

def top_score(question):
  vector_list = model.encode([question])
  query_vector = vector_list[0]
  return max(cosine_similarity(query_vector, v) for v in vectors)


def gate_score(question):
  full_question_score = top_score(question)
  stripped = strip_game_words(question)
  stripped_score = top_score(stripped)
  return max(full_question_score, stripped_score)

def answer_with_game(question):
  fixed = fix_typos(question, vocabulary)
  score = float(gate_score(fixed))
  game = detect_game(question, default=None)
  game_chunks, search = make_game_search(chunks, vectors, game, model.encode)
  result = answer_question(fixed, game_chunks, search, lambda q: score, call_claude)
  return {**result, "game": game, "score": score}

from app import create_app
import uvicorn
app = create_app(answer_with_game, "logs/questions.jsonl")
# Locally: 127.0.0.1:8000. In the container the Dockerfile sets HOST=0.0.0.0 and PORT=7860.
uvicorn.run(app, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")))
