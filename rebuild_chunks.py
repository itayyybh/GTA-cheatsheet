from pathlib import Path
from cheatsheet import ingest, save_chunks

files = Path("data/cache").glob("*.json")
titles = []

for file in files:
  title = file.stem.replace("_", " ")
  titles.append(title)

chunks = ingest(titles, "https://gta.wiki", "data/cache")
print(len(chunks))
print(chunks[5])
save_chunks(chunks, "data/chunks.json")
