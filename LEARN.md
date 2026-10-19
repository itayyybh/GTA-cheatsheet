# 💡 Learn — glossary

Every 💡 Learn item from our sessions, grouped by topic. Each entry is tied to something we actually built or measured.
New items go under the matching topic; a concept appears once.

---

## Retrieval (finding the right chunks)

**BM25** — Keyword (lexical) search that scores chunks by matching words, giving rare words more weight. A smarter version of your `keyword_search`; it was the first baseline in the Tavo codebase RAG.

**Dense retrieval** — Search by meaning using embeddings (Tavo RAG used `bge-small`; GTA Week 3 uses `all-MiniLM-L6-v2`). Matches "how much" to "price", which keyword search can't.

**Hybrid search (RRF)** — Run keyword and dense search, then merge the two ranked lists. Reciprocal Rank Fusion rewards chunks ranked high in either list. In Tavo RAG it clearly improved retrieval but not final answer correctness.

**Agentic RAG** — Instead of always retrieving once, the model decides whether to search, what to search for, and whether to search again, calling retrieval as a tool in a loop. Basic RAG: your code controls the search. Agentic RAG: the AI controls it.

---

## Evaluation (knowing whether a change helped)

**Golden set** — A fixed list of questions with known good answers (your `golden.json`, 31 questions) that you rerun after every change, so "better" is a number instead of a feeling.

**Baseline** — The score of the simplest working version, recorded before you change anything. Every later fix is judged by how far it moves that number. GTA: 0.516 → 0.677 (stopwords) → 0.774 (stripping `?`). For an agentic version, the baseline is your best non-agentic setup, not the first number.

**Evaluation harness** — A script you rerun unchanged after every change to the system. That's what `eval.py` (formerly `baseline.py`) is: the tool that produces the numbers, not the baseline itself.

**Trajectory** — The full sequence of tool calls an agent made for one question. Evaluating an agent means checking the answer *and* the trajectory: did it search for the right thing, and did it stop at the right time?

---

## Agents (the loop)

**Tool calling** — The model doesn't run a tool itself. It outputs a request like `search("Adder price")`, your code runs `keyword_search` and hands the results back, and the model continues.

**Agent loop** — A `while` loop: the model either asks for a tool (your code runs it and appends the result) or gives a final answer, which ends the loop. Each pass is one turn.

**ReAct** — The common name for the pattern: **Re**ason ("I need the price"), **Act** (call the tool), observe the result, repeat.

**Stop condition** — How the loop ends. Normally the model decides it has enough, but you always add a hard limit ("max 5 tool calls") so a confused model can't search forever.

---

## Cost and performance

**Cost** — You pay per token. Every extra search round sends more retrieved text and more model calls, so an agentic answer that searches three times can cost several times the one-shot version.

**Latency** — The time from the player's question to the answer appearing. A gamer mid-mission feels the difference between 2 seconds and 8.

**End-to-end latency** — The total wait including every tool call and network hop, not just text generation. Example: a 41-second chat reply that requested folder access, read files and searched past chats before writing.

**Context growth** — Every tool result is appended to the conversation, and the whole thing is sent again each turn, so turn 4 costs more than turn 1. The main reason agentic RAG costs more than one search.

**Model routing** — Sending easy questions to a cheap, fast model and hard ones to a strong, expensive one.

**Prompt caching** — Reusing the processed part of a prompt that repeats every call (instructions, fixed context), so you don't pay full price for it each time.

**Cost/quality trade-off** — Showing with numbers that a cheaper setup keeps, say, 95% of the quality at 30% of the price. Impossible without an eval set — which is why your golden set matters for these jobs.
