# Audit Log

Every attribution decision and every appeal is captured as a structured JSON line in `logs/audit.jsonl`. One JSON object per line (JSONL format) makes appending easy and parsing straightforward.

The `GET /log` endpoint returns recent entries for grading and README evidence.

## Storage

| File | Purpose |
|------|---------|
| `logs/audit.jsonl` | Append-only audit trail (submission + appeal events) |
| `data/submissions.json` | Current state of each submission (used for appeals) |

## Submission Event Schema

Written when `POST /submit` completes.

| Field | Type | Description |
|-------|------|-------------|
| `event_type` | string | Always `"submission"` |
| `timestamp` | string | UTC ISO 8601, e.g. `2026-06-25T14:32:10.123Z` |
| `content_id` | string | UUID for this submission |
| `creator_id` | string | Creator who submitted the text |
| `status` | string | `"classified"` on initial submission |
| `attribution` | string | `"likely_ai"`, `"likely_human"`, or `"uncertain"` |
| `confidence` | float | Combined AI-likelihood score (`0.0`–`1.0`) |
| `llm_score` | float | Signal 1 score |
| `llm_reason` | string | Short explanation from the LLM signal |
| `stylometric_score` | float | Signal 2 score |
| `stylometric_features` | object | Raw feature values (`sentence_length_variance`, `type_token_ratio`, `punctuation_density`) |

**Example:**

```json
{
  "event_type": "submission",
  "timestamp": "2026-06-25T14:32:10.123Z",
  "content_id": "3f7a2b1e-8c4d-4f1a-9b2e-1a2b3c4d5e6f",
  "creator_id": "test-user-1",
  "status": "classified",
  "attribution": "likely_ai",
  "confidence": 0.78,
  "llm_score": 0.81,
  "llm_reason": "The text uses generic transitions and highly uniform phrasing.",
  "stylometric_score": 0.72,
  "stylometric_features": {
    "sentence_length_variance": 4.2,
    "type_token_ratio": 0.48,
    "punctuation_density": 0.03
  }
}
```

## Appeal Event Schema

Written when `POST /appeal` is accepted.

| Field | Type | Description |
|-------|------|-------------|
| `event_type` | string | Always `"appeal"` |
| `timestamp` | string | UTC ISO 8601 |
| `content_id` | string | UUID of the appealed submission |
| `creator_id` | string | Creator from the original submission |
| `status` | string | `"under_review"` after appeal |
| `attribution` | string | Original attribution (unchanged) |
| `confidence` | float | Original combined score (unchanged) |
| `llm_score` | float | Original LLM signal score |
| `stylometric_score` | float | Original stylometric signal score |
| `appeal_reasoning` | string | Creator's explanation for the appeal |

**Example:**

```json
{
  "event_type": "appeal",
  "timestamp": "2026-06-25T15:10:00.456Z",
  "content_id": "3f7a2b1e-8c4d-4f1a-9b2e-1a2b3c4d5e6f",
  "creator_id": "test-user-1",
  "status": "under_review",
  "attribution": "likely_ai",
  "confidence": 0.78,
  "llm_score": 0.81,
  "stylometric_score": 0.72,
  "appeal_reasoning": "I wrote this myself from personal experience."
}
```

## What a Human Reviewer Would See

When opening the appeal queue, a reviewer needs:

1. The original submitted text (from `data/submissions.json`)
2. The transparency label and attribution bucket
3. Combined confidence score and individual signal scores
4. LLM reason and stylometric features
5. The creator's appeal reasoning
6. Timestamps for submission and appeal events
