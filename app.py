from cheatsheet import validate_question, source_links,  log_entry, append_jsonl, log_summary, read_jsonl, check_rate

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from datetime import datetime, timezone
import time

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GTA Cheatsheet</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 640px; margin: 40px auto; padding: 0 16px; background: #111; color: #eee; }
  h1 { font-size: 1.6rem; margin-bottom: 4px; }
  .sub { color: #999; margin-top: 0; }
  form { display: flex; gap: 8px; margin: 24px 0; }
  input { flex: 1; padding: 10px; font-size: 1rem; border-radius: 6px; border: 1px solid #444; background: #1c1c1c; color: #eee; }
  button { padding: 10px 16px; font-size: 1rem; border-radius: 6px; border: 0; background: #2e7d32; color: white; cursor: pointer; }
  button:disabled { opacity: 0.5; cursor: default; }
  #answer { white-space: pre-wrap; line-height: 1.5; }
  .refused { color: #999; font-style: italic; }
  .meta { color: #999; font-size: 0.85rem; }
  a { color: #81c784; }
  footer { margin-top: 40px; color: #777; font-size: 0.8rem; }
</style>
</head>
<body>
  <h1>GTA Cheatsheet</h1>
  <p class="sub">Ask about GTA V, GTA Online and the GTA VI trailers. Answers come only from saved wiki pages.</p>

  <form id="ask">
    <input id="question" placeholder="e.g. how much do sticky bombs cost in gta 5" autocomplete="off" autofocus>
    <button id="go">Ask</button>
  </form>

  <p id="meta" class="meta"></p>
  <p id="answer"></p>
  <ul id="sources"></ul>

  <footer>
    Covers 21 hand-saved wiki pages about GTA V, GTA Online and the GTA VI trailers, so many questions will get "Not documented yet."<br>
    Questions are logged to improve the answers. There are no accounts; please don't type personal information.<br>
    Text from <a href="https://gta.wiki" target="_blank">gta.wiki</a>, CC BY-NC-SA 3.0. Each answer links to the pages it used. Non-commercial learning project.
  </footer>

<script>
const form = document.getElementById("ask");
const input = document.getElementById("question");
const button = document.getElementById("go");
const answer = document.getElementById("answer");
const meta = document.getElementById("meta");
const sources = document.getElementById("sources");

const ERRORS = {
  empty: "Type a question first.",
  too_long: "That question is too long (300 characters max).",
  model_unavailable: "The answer service is unavailable right now. Try again in a moment.",
  rate_limited: "Too many questions in a row. Wait a minute and try again.",
};

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = input.value;

  button.disabled = true;
  answer.className = "";
  answer.textContent = "Thinking...";
  meta.textContent = "";
  sources.innerHTML = "";

  try {
    const res = await fetch("/ask", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({question: question}),
    });
    const data = await res.json();

    if (!res.ok) {
      answer.className = "refused";
      answer.textContent = ERRORS[data.error] || "Something went wrong.";
      return;
    }

    answer.className = data.refused ? "refused" : "";
    answer.textContent = data.answer;
    if (data.game) meta.textContent = "Game: " + data.game;

    for (const s of data.sources) {
      const a = document.createElement("a");
      a.href = s.url;
      a.textContent = s.title;
      a.target = "_blank";
      const li = document.createElement("li");
      li.appendChild(a);
      sources.appendChild(li);
    }
  } catch (err) {
    answer.className = "refused";
    answer.textContent = "Could not reach the server.";
  } finally {
    button.disabled = false;
  }
});
</script>
</body>
</html>
"""

class Question(BaseModel):
  question : str

def create_app(answer_fn, log_path, max_per_minute=10, clock=time.monotonic):
  app = FastAPI()


  @app.get("/", response_class=HTMLResponse)
  def home():
    return PAGE

  req_times = {}
  @app.post("/ask")
  def ask(body: Question, request: Request):
    visitor = request.headers.get("x-forwarded-for")
    if visitor is not None:
      visitor = visitor.split(",")[0].strip()
    else:
      visitor = request.client.host

    history = req_times.get(visitor, [])

    allowed, updated_list = check_rate(history, clock(), max_per_minute)
    req_times[visitor] = updated_list

    if not allowed:
      return JSONResponse({"error": "rate_limited"}, status_code=429)
      
  
    question, error = validate_question(body.question)
    if error:
      return JSONResponse({"error": error}, status_code=400)
    
    when = datetime.now(timezone.utc).isoformat(timespec="seconds")
    start = time.perf_counter()
    try:
      result = answer_fn(question)
    except Exception as e:
      seconds = time.perf_counter() - start
      entry = log_entry(question, {"answer": "", "sources": [], "refused": True}, None, seconds, when, error=type(e).__name__)
      entry["score"] = None
      append_jsonl(log_path, entry)
      return JSONResponse({"error": "model_unavailable"}, status_code=503)
    
    seconds = time.perf_counter() - start
    entry = log_entry(question, result, result.get("game"), seconds, when)
    score = result.get("score") 
    if score is not None:
      entry["score"] = round(score, 3)
    else:
      entry["score"] = None

    append_jsonl(log_path, entry)

    return {"answer": result["answer"], "refused": result["refused"], "game": result.get("game"), "sources": source_links(result["sources"])}

  @app.get("/stats")
  def stats():
    return log_summary(read_jsonl(log_path))
  
  return app