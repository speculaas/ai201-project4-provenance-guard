# Development History

Milestone log for Provenance Guard. Update this file as each phase completes so the repo shows planning and implementation evolving together.

## M1: Planning and Repository Setup

**Goal:** Understand the assignment, choose detection signals, and initialize the repo.

**Files touched:** `planning.md`, `README.md`, `requirements.txt`, `.env.example`, `.gitignore`

**What was implemented:**
- Project planning document with detection signals, uncertainty thresholds, label text, appeals workflow, and edge cases
- Python dependency list (Flask, Flask-Limiter, Groq, python-dotenv)
- Initial commit with repo structure

**How to verify:**
- `planning.md` answers all five spec questions
- Virtual environment installs cleanly with `pip install -r requirements.txt`

---

## M2: Architecture and API Design

**Goal:** Document system architecture with Mermaid diagrams and define the API contract.

**Files touched:** `docs/architecture.md`, `docs/api-flow.md`, `docs/audit-log.md`, `examples/`

**What was implemented:**
- System flowchart (submit path)
- Component responsibility diagram
- Sequence diagrams for `/submit` and `/appeal`
- API endpoint documentation with example JSON
- Audit log schema documentation

**How to verify:**
- Mermaid diagrams render on GitHub (open `docs/architecture.md` in the repo)
- API docs match the routes in `app.py`

---

## M3: Submission Endpoint and First Signal

**Goal:** Flask app with `POST /submit`, Groq LLM authorship signal, and basic audit logging.

**Files touched:** `app.py`, `detector.py`, `audit.py`

**What was implemented:**
- `POST /submit` accepts `text` + `creator_id`, returns `content_id`, attribution, confidence, label
- `llm_authorship_signal()` calls Groq (with neutral fallback if API key missing)
- `GET /log` returns recent audit entries
- Each submission appends a structured JSONL entry

**How to verify:**
```bash
curl -s -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "sample text here", "creator_id": "test-user-1"}' | python -m json.tool
```
Response includes `content_id`, `attribution`, `confidence`, and `label`.

---

## M4: Stylometric Signal and Confidence Scoring

**Goal:** Second detection signal and combined confidence scoring with three attribution buckets.

**Files touched:** `detector.py`, `scoring.py`, `audit.py`

**What was implemented:**
- `stylometric_signal()` computes sentence-length variance, type-token ratio, punctuation density
- `combine_signal_scores()` weighted average: `0.65 * llm + 0.35 * stylometric`
- `classify_from_score()` maps to `likely_human` / `uncertain` / `likely_ai`
- Audit log records both individual signal scores

**How to verify:**
- Submit clearly AI-like, clearly human-like, and borderline texts (see `examples/test_inputs.md`)
- Scores should differ meaningfully across categories
- `GET /log` shows `llm_score` and `stylometric_score` for each entry

---

## M5: Appeals, Labels, Audit Logging, README Polish

**Goal:** Production layer — transparency labels, appeals workflow, rate limiting, complete audit trail.

**Files touched:** `labels.py`, `app.py`, `audit.py`, `README.md`

**What was implemented:**
- Three transparency label variants in `labels.py`
- `POST /appeal` updates status to `under_review` and logs appeal event
- Rate limiting on `POST /submit` (`10 per minute; 100 per day`)
- Full audit log with submission and appeal events

**How to verify:**
- All three label variants reachable with different test inputs
- Appeal with a saved `content_id` returns `status: under_review`
- `GET /log` shows both submission and appeal entries
- Rapid-fire 12 requests to `/submit` produces `429` after the 10th

---

## M6: Documentation and Portfolio (pending)

**Goal:** Final README with rubric sections, confidence scoring examples, rate-limit evidence, and portfolio walkthrough video.

**Files to touch:** `README.md`, `docs/development-history.md`

**What remains:**
- Two example submissions with noticeably different confidence scores in README
- Rate-limit reasoning and 429 evidence
- Known limitations section
- Spec reflection and AI usage sections
- Portfolio walkthrough video
