# Build data/index.json (the chunk embeddings) ahead of time.
# Used by the Dockerfile so the deployed app never has to embed at startup.
# Run from the project root: python -m runs.build_index
from pathlib import Path

from sentence_transformers import SentenceTransformer

from cheatsheet import load_chunks, embed_chunks, save_index

MODEL_NAME = "all-MiniLM-L6-v2"   # must match runs/serve.py

chunks = load_chunks("data/chunks.json")
model = SentenceTransformer(MODEL_NAME)
vectors = embed_chunks(chunks, model.encode, batch_size=32)
save_index(Path("data/index.json"), MODEL_NAME, chunks, vectors)
print(f"index built: {len(vectors)} vectors")
