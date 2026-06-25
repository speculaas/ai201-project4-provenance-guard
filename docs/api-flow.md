# API Flow

Provenance Guard exposes a small Flask API. All endpoints return JSON.

Base URL (local development): `http://localhost:5000`

## `GET /`

Health/discovery endpoint listing available routes.

**Response:**

```json
{
  "message": "Provenance Guard API",
  "endpoints": ["POST /submit", "POST /appeal", "GET /log"]
}
```

## `POST /submit`

Accepts a text submission for attribution analysis. Rate-limited to `10 per minute; 100 per day`.

**Request body:**

```json
{
  "text": "The sun dipped below the horizon, painting the sky in hues of amber and rose.",
  "creator_id": "test-user-1"
}
```

**Success response (`200`):**

```json
{
  "content_id": "3f7a2b1e-8c4d-4f1a-9b2e-1a2b3c4d5e6f",
  "status": "classified",
  "attribution": "likely_ai",
  "confidence": 0.78,
  "label": "This post was flagged as likely AI-generated. Our system saw multiple signals that matched machine-generated writing patterns, so readers should treat authorship as likely assisted or produced by AI.",
  "signals": {
    "llm_score": 0.81,
    "llm_reason": "The text uses generic transitions and highly uniform phrasing.",
    "stylometric_score": 0.72,
    "stylometric_features": {
      "sentence_length_variance": 4.2,
      "type_token_ratio": 0.48,
      "punctuation_density": 0.03
    }
  }
}
```

**Error responses:**

| Status | Condition |
|--------|-----------|
| `400` | Missing `text` or `creator_id` |
| `429` | Rate limit exceeded |

## `POST /appeal`

Lets a creator contest a classification. Does not re-run detection.

**Request body:**

```json
{
  "content_id": "3f7a2b1e-8c4d-4f1a-9b2e-1a2b3c4d5e6f",
  "creator_reasoning": "I wrote this myself from personal experience. I am a non-native English speaker and my writing style may appear more formal than typical."
}
```

**Success response (`200`):**

```json
{
  "message": "Appeal received and marked for review.",
  "content_id": "3f7a2b1e-8c4d-4f1a-9b2e-1a2b3c4d5e6f",
  "status": "under_review",
  "appeal_reasoning": "I wrote this myself from personal experience. I am a non-native English speaker and my writing style may appear more formal than typical."
}
```

**Error responses:**

| Status | Condition |
|--------|-----------|
| `400` | Missing `content_id` or `creator_reasoning` |
| `404` | `content_id` not found |

## `GET /log`

Returns the most recent structured audit log entries (up to 25).

**Response:**

```json
{
  "entries": [
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
  ]
}
```
