from cheatsheet import validate_question, source_links,  log_entry, append_jsonl, log_summary, read_jsonl

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from datetime import datetime, timezone
import time

class Question(BaseModel):
  question : str

def create_app(answer_fn, log_path):
  app = FastAPI()

  @app.get("/", response_class=HTMLResponse)
  def home():
    return "<form> GTA cheatsheet</form>"

  @app.post("/ask")
  def ask(body: Question):
    question, error = validate_question(body.question)
    if error:
      return JSONResponse({"error": error}, status_code=400)
    
    when = datetime.now(timezone.utc).isoformat(timespec="seconds")
    start = time.perf_counter()
    try:
      result = answer_fn(question)
    except Exception as e:
      seconds = time.perf_counter() - start
      append_jsonl(log_path, log_entry(question, {"answer": "", "sources": [], "refused": True}, None, seconds, when, error=type(e).__name__))
      return JSONResponse({"error": "model_unavailable"}, status_code=503)
    
    seconds = time.perf_counter() - start
    append_jsonl(log_path, log_entry(question, result, result.get("game"), seconds, when))

    return {"answer": result["answer"], "refused": result["refused"], "game": result.get("game"), "sources": source_links(result["sources"])}

  @app.get("/stats")
  def stats():
    return log_summary(read_jsonl(log_path))
  
  return app