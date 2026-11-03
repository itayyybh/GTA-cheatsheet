# Go / no-go: put the GTA Cheatsheet online for launch week

**Decision date:** 2026-11-13. **Launch:** 2026-11-19.
**Written:** 2026-11-03, before the final measurements, so the thresholds can't be moved to fit the result afterwards.

**Decision rule**
- **Go** if every **must** passes.
- **No-go** if any **must** fails: the project stays a portfolio demo (README + video), and the next step is the agentic experiment (Week 8).
- **Should** items don't block a go, but each one that fails is written down as a known limitation on the page or in the README.

## 1. Quality

| # | Criterion | Threshold | Level | Status 2026-11-03 | Measured by |
|---|---|---|---|---|---|
| Q1 | Answers correct, holdout + unanswerable (44), by hand | ≥ 0.85 | must | ✅ 38/44 = 0.86 (2026-11-03, with `fix_typos`) | `runs/week5_run.py`, hand grading |
| Q2 | Unanswerable questions refused | 14/14 | must | ✅ 14/14 | same run |
| Q3 | Wrong-game answers on the trap set (10) | 0 | must | ✅ 0 | trap run |
| Q4 | Trap set correct | ≥ 8/10 | should | ✅ 9/10 | trap run |
| Q5 | Real questions behaving as expected (web log) | ≥ 80% | should | ✅ 33/36 = 92% after `fix_typos` (2026-11-03; was 28/36) | `logs/questions.jsonl`, by hand |
| Q6 | Name typos refused at the gate (typo eval set) | ≤ 1 in 5 | should | ✅ 0/12 refused with `fix_typos` (was 8/12), 2026-11-03 | `eval/golden_typos.json` |

## 2. Reliability

| # | Criterion | Threshold | Level | Status | Measured by |
|---|---|---|---|---|---|
| R1 | Errors (503s) over ≥ 50 logged questions | 0 | must | ✅ 0 / 53 | `/stats` |
| R2 | Latency, answered questions, p95 | ≤ 7 s | must | ✅ 6.4 s (median 3.0 s) | log `seconds` |
| R3 | Model outage gives a clear message, no crash | yes | must | ✅ test `test_week6_app_model_error_is_503_and_logged` | `pytest` |
| R4 | All tests pass | 143/143 | must | ⏳ re-run on the final commit | `pytest` |

## 3. Safety and honesty

| # | Criterion | Threshold | Level | Status | Measured by |
|---|---|---|---|---|---|
| S1 | Hostile prompts not obeyed (instructions, opinion, system prompt, role play) | 5/5 | must | ✅ none obeyed; 1 ignored the plain-text rule | the 5 hostile questions |
| S2 | Every answer links its source pages | 100% | must | ✅ answers without a valid citation are refused | `answer_question` + `source_links` |
| S3 | Licence credit visible on the page (CC BY-NC-SA, gta.wiki) | yes | must | ✅ footer | the page |
| S4 | Answer shown as text, not HTML (no XSS) | yes | must | ✅ `textContent` | `app.py` |

## 4. Cost

| # | Criterion | Threshold | Level | Status | Measured by |
|---|---|---|---|---|---|
| C1 | Cost per answered question | ≤ $0.001 | must | ✅ ≈ $0.0004 | token counts in the runs |
| C2 | Hard spending cap on the API key | set | must (if public) | ⏳ | Anthropic console spend limit |

## 5. Going public (only matters if 1–4 pass)

| # | Criterion | Level | Status |
|---|---|---|---|
| P1 | Runs on a host, reachable by URL, survives a restart | must | ⏳ deployed to Cloud Run 2026-11-03 (us-central1, 2 GiB, max 1 instance); live test pending |
| P2 | API key only on the server (environment variable, never in the page or the repo) | must | ✅ locally (`.env`, git-ignored); ✅ Cloud Run reads it from Secret Manager |
| P3 | Rate limit per visitor (e.g. 10 questions / minute) | must | ✅ 10/min per visitor (`x-forwarded-for`), 429, tested (2026-11-03) |
| P4 | Privacy line on the page: questions are logged, no accounts, don't type personal data | must | ✅ footer (2026-11-03) |
| P5 | Non-commercial: no ads, no payments (licence is NC) | must | ✅ |
| P6 | Page says what it covers: 21 GTA V / Online pages + GTA VI trailer facts | should | ✅ footer (2026-11-03) |
| P7 | GTA VI launch plan: which pages to hand-save after 2026-11-19, and who does it | should | ⏳ |

## Before 2026-11-13

1. Add the gate `score` to `log_entry`, so gate refusals and Claude refusals can be told apart (Q5, Q6).
2. Typo correction for names against the 21 page titles; build a small typo eval set (Q6).
3. Re-run the 44 set and the trap set on the final code (Q1–Q4); re-run `pytest` (R4).
4. Only if 1–4 look like a go: deploy test, rate limit, spend cap, privacy line (C2, P1–P4).

## Decision (fill in on 2026-11-13)

- Result: GO / NO-GO
- Musts failed:
- Shoulds failed (known limitations):
- Reason, in one sentence:
