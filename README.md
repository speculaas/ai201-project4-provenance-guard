# Provenance Guard

Backend service for AI201 Project 4. A creative platform submits text; Provenance Guard runs two detection signals, returns a confidence score and transparency label, logs the decision, and supports creator appeals.

**API:** `POST /submit` · `POST /appeal` · `GET /log`

See [docs/architecture.md](docs/architecture.md) for Mermaid diagrams and [docs/verification-runbook.md](docs/verification-runbook.md) for the test procedure.

## Architecture Overview

1. Client sends `text` + `creator_id` to `POST /submit`.
2. **Signal 1 (Groq LLM)** returns an AI-likelihood score and short reason.
3. **Signal 2 (stylometric)** returns a score from structural features + AI boilerplate phrase density.
4. **Scoring** combines signals (`80/20` weighting, with disagreement and template-AI overrides).
5. **Labels** map the score to `likely_ai`, `likely_human`, or `uncertain` and return plain-language text.
6. **Audit log** stores the decision; creators can `POST /appeal` to move status to `under_review`.

## Detection Signals

### Signal 1: Groq LLM authorship judge (`detector.py`)

- **Measures:** holistic style — generic transitions, hedged phrasing, lack of personal voice, overly polished structure.
- **Why chosen:** recommended by the project spec; same LLM-as-judge pattern as the RepairSafe lab.
- **What it misses:** formal human writing, non-native English, and lightly edited human work can look AI-like to the model.

### Signal 2: Stylometric heuristics (`detector.py`)

- **Measures:** sentence-length variance, type-token ratio, punctuation density, and **AI boilerplate phrase density** (e.g. "Furthermore," "it is important to note," "stakeholders").
- **Why chosen:** independent from the LLM, pure Python, fast, and explainable in the audit log.
- **What it misses:** short texts (falls back to neutral `0.5`), poetry/repetition, and formal human prose without boilerplate phrases.

Boilerplate density was added after calibration showed that structural metrics alone scored polished AI prose as human-like (high vocabulary diversity + sentence variance).

## Confidence Scoring

Combined score = AI-likelihood from `0.0` (likely human) to `1.0` (likely AI).

| Score range | Attribution | Label |
|-------------|-------------|-------|
| ≥ 0.75 | `likely_ai` | High-confidence AI |
| 0.36 – 0.74 | `uncertain` | Uncertain |
| ≤ 0.35 | `likely_human` | High-confidence human |

The uncertain band is intentionally wide because false positives (flagging human writers as AI) are more harmful than false negatives on a writing platform.

**How validated:** Ran the course spec calibration samples (see `examples/test_inputs.md`) through `POST /submit` on 2026-07-01. Scores separated clearly between obvious AI and obvious human cases; borderline formal writing landed in `uncertain`.

### Example 1 — high-confidence AI

- **Input:** "Artificial intelligence represents a transformative paradigm shift in modern society. It is important to note… Furthermore, stakeholders…"
- **attribution:** `likely_ai`
- **confidence:** `0.94`
- **llm_score:** `0.9`
- **stylometric_score:** `0.608` (7 boilerplate hits)

### Example 2 — high-confidence human

- **Input:** "ok so i finally tried that new ramen place downtown and honestly? underwhelming…"
- **attribution:** `likely_human`
- **confidence:** `0.095`
- **llm_score:** `0.1`
- **stylometric_score:** `0.076`

The gap between `0.94` and `0.095` shows the scorer produces meaningfully different outputs, not a constant score.

## Transparency Label Text

| Variant | Exact text |
|---------|------------|
| High-confidence AI | This post was flagged as likely AI-generated. Our system saw multiple signals that matched machine-generated writing patterns, so readers should treat authorship as likely assisted or produced by AI. |
| High-confidence human | This post appears likely human-written. Our system found enough variation and human-like writing signals to avoid flagging it as AI-generated, but this is still a probabilistic judgment. |
| Uncertain | Our system found mixed evidence and cannot confidently say whether this post was human-written or AI-generated. Readers should treat the attribution as unresolved rather than definitive. |

All three variants were reached in verification testing (`03_submit_likely_ai`, `04_submit_likely_human`, `05_submit_uncertain`).

## Rate Limiting

**Limits on `POST /submit`:** `10 per minute; 100 per day` (Flask-Limiter, in-memory storage).

**Reasoning:** A single creator might submit a few drafts in a short session; `10/minute` allows normal use while blocking scripted flooding. `100/day` caps sustained abuse from one IP without affecting typical homework/demo usage.

**Evidence (2026-07-01):**

```text
request 1: 200
request 2: 200
...
request 10: 200
request 11: 429
request 12: 429
```

## Appeals Workflow

`POST /appeal` accepts `content_id` + `creator_reasoning`, sets status to `under_review`, and appends an appeal event to the audit log. No automatic re-classification.

**Example response:**

```json
{
  "message": "Appeal received and marked for review.",
  "content_id": "ded3e282-f49d-4d8d-859c-758127510d6d",
  "status": "under_review",
  "appeal_reasoning": "I wrote this myself from personal experience. I am a non-native English speaker and my writing style may appear more formal than typical."
}
```

## Audit Log Sample

Three representative entries from `GET /log` (2026-07-01 run):

**Submission — likely AI:**

```json
{
  "event_type": "submission",
  "timestamp": "2026-07-01T04:34:45Z",
  "content_id": "a66aeb37-2c9a-4bb1-b818-f077d4b0040f",
  "creator_id": "test-ai",
  "status": "classified",
  "attribution": "likely_ai",
  "confidence": 0.94,
  "llm_score": 0.9,
  "llm_reason": "The text features generic transitions and hedged balanced phrasing typical of AI-generated content.",
  "stylometric_score": 0.608,
  "stylometric_features": {
    "boilerplate_hits": 7,
    "boilerplate_score": 1.0,
    "sentence_length_variance": 29.556,
    "type_token_ratio": 0.884,
    "punctuation_density": 0.047
  }
}
```

**Submission — likely human:**

```json
{
  "event_type": "submission",
  "timestamp": "2026-07-01T04:34:52Z",
  "content_id": "9e7179b3-980c-48b1-8a2c-f5b1e5b8d094",
  "creator_id": "test-human",
  "status": "classified",
  "attribution": "likely_human",
  "confidence": 0.095,
  "llm_score": 0.1,
  "stylometric_score": 0.076
}
```

**Appeal:**

```json
{
  "event_type": "appeal",
  "timestamp": "2026-07-01T04:35:21.158266Z",
  "content_id": "ded3e282-f49d-4d8d-859c-758127510d6d",
  "creator_id": "test-user-1",
  "status": "under_review",
  "attribution": "uncertain",
  "confidence": 0.42,
  "appeal_reasoning": "I wrote this myself from personal experience. I am a non-native English speaker and my writing style may appear more formal than typical."
}
```

## Known Limitations

**Formal academic prose without AI boilerplate** can score mid-high on the LLM signal while stylometrics stay low. In testing, the monetary-policy sample received `uncertain` at confidence `0.715` (`llm_score: 0.8`, `stylometric_score: 0.09`) — not a false-positive `likely_ai`, but still elevated. This is why the wide uncertain band and appeals path matter.

**Very short submissions** (one sentence, &lt;20 words) cannot produce stable stylometric features and fall back to a neutral `0.5` score.

## Spec Reflection

**How the spec helped:** Milestone structure pushed planning before code, required two genuinely distinct signals, and required uncertainty labels rather than binary output. That led directly to the three-bucket design and appeals workflow.

**Where implementation diverged:** Initial stylometric scoring used only structural uniformity (variance/TTR/punctuation). Calibration showed polished AI prose scored as human-like structurally, so boilerplate phrase density and rebalanced weights were added — a divergence driven by test results, documented in `planning.md`.

## AI Usage

1. **Project scaffold (Cursor):** Directed Cursor to create the Flask app structure, detection modules, and `planning.md` from the project spec. Revised the initial `65/35` weighting after calibration showed formal AI samples could never reach `likely_ai`.
2. **Scoring fix (Cursor):** After `03_submit_likely_ai` returned `uncertain` at `0.435`, asked Cursor to diagnose signal disagreement and implement boilerplate detection + `80/20` weights. Verified the full AI paragraph then returned `likely_ai` at `0.94`.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add GROQ_API_KEY
python app.py
```

Server binds to `0.0.0.0:5000` by default. See [examples/sample_requests.md](examples/sample_requests.md) for curl commands.

## Still To Do Before Submission

- [ ] Optional: run calibration test 12 (lightly edited AI) from `docs/verification-runbook.md` section 2
- [ ] Record portfolio walkthrough video (~2 min)
- [ ] Submit repo link via Course Portal
