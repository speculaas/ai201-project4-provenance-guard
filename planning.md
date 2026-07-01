# Provenance Guard Planning

## Overview
Provenance Guard is a backend service for a creative platform that accepts a text submission, runs multiple attribution signals, converts those signals into a confidence score, returns a transparency label, and stores the decision in a structured audit log. If a creator believes the result is wrong, they can file an appeal that moves the submission to `under_review` and appends a second audit event.

## Detection Signals
### Signal 1: Groq LLM authorship judge
- **What it measures:** holistic semantic and stylistic patterns that often appear in AI-generated writing, such as generic transitions, overly balanced structure, vague specificity, and low personal voice.
- **Output format:** a score from `0.0` to `1.0` where higher means "more likely AI-generated," plus a short reason string.
- **Why I chose it:** the spec recommends Groq, and the RepairSafe lab already uses the pattern of prompting an LLM to make a structured classification judgment.
- **Blind spots:** it can over-flag polished, formal, edited, or non-native-English human writing.

### Signal 2: Stylometric heuristics
- **What it measures:** structural and lexical features of the text that can be computed without another model call.
- **Metrics:** sentence-length variance, type-token ratio, punctuation density, plus **AI boilerplate phrase density** (e.g. "Furthermore," "it is important to note," "stakeholders").
- **Output format:** a score from `0.0` to `1.0` where higher means "more likely AI-generated," plus the raw feature values.
- **Why I chose it:** it is a genuinely distinct signal from the LLM judgment and aligns with the project's recommended stack.
- **Blind spots:** short texts, poetry, and intentionally minimal writing can look unusually uniform even when fully human-written. Pure structural metrics alone can misread polished formal AI as human (high variance + rich vocabulary); boilerplate density was added to address that.

### Combination Strategy
I combine the signals with a weighted average:

`combined_score = 0.80 * llm_score + 0.20 * stylometric_score`

When the signals disagree by more than `0.45`, the LLM weight increases to `0.88` so polished template AI prose is not dragged into `uncertain` by structural false negatives.

When boilerplate density is very high (`>= 0.85`) and the LLM score is at least `0.55`, a template-AI blend can raise the combined score: `0.60 * llm + 0.40 * boilerplate`.

The LLM gets more weight because it captures higher-level style and meaning, while the stylometric signal acts as an independent structural and lexical check.

## Uncertainty Representation
- `0.00 - 0.35`: likely human
- `0.36 - 0.74`: uncertain
- `0.75 - 1.00`: likely AI

In this system, a confidence score is an AI-likelihood score, not a truth claim. A `0.60` means the system sees some AI-like signals, but not enough to confidently label the work as AI-generated. Because false positives are more harmful than false negatives on a writing platform, the uncertain band is intentionally wide.

## Transparency Label Design
These are the exact text variants the API will return.

### High-confidence AI
> This post was flagged as likely AI-generated. Our system saw multiple signals that matched machine-generated writing patterns, so readers should treat authorship as likely assisted or produced by AI.

### High-confidence human
> This post appears likely human-written. Our system found enough variation and human-like writing signals to avoid flagging it as AI-generated, but this is still a probabilistic judgment.

### Uncertain
> Our system found mixed evidence and cannot confidently say whether this post was human-written or AI-generated. Readers should treat the attribution as unresolved rather than definitive.

## Appeals Workflow
- **Who can appeal:** the creator associated with the original submission.
- **Required fields:** `content_id` and `creator_reasoning`.
- **System behavior on appeal:** locate the stored submission, set `status` to `under_review`, store the creator's explanation, append an `appeal` event to the audit log, and return a confirmation response.
- **What a human reviewer would need:** the original text, original label, combined confidence score, individual signal scores, model explanation, and the creator's appeal reasoning.

## Anticipated Edge Cases
1. A poem with deliberate repetition, sparse punctuation, and short lines may look statistically uniform and receive an inflated AI-likelihood score.
2. A carefully edited essay by a non-native English speaker may sound formal and generic enough that the LLM signal overestimates AI involvement.
3. Very short submissions can be too small for stable stylometric analysis, so the starter falls back to a neutral heuristic score.

## Architecture

Mermaid diagrams (flowchart, component map, sequence diagrams) live in [docs/architecture.md](docs/architecture.md). The ASCII summary below is the planning baseline.

```text
POST /submit
  -> validate JSON body
  -> LLM authorship signal
  -> stylometric signal
  -> confidence scoring
  -> transparency label selection
  -> save submission record
  -> append audit log entry
  -> return JSON response

POST /appeal
  -> validate JSON body
  -> lookup content_id
  -> update status to under_review
  -> store creator_reasoning
  -> append audit log entry
  -> return confirmation JSON
```

The submission flow starts with raw text and creator metadata, turns that into two signal scores, merges them into a single AI-likelihood score, and maps that score to a plain-language label. The appeal flow reuses the stored `content_id`, preserves the original decision, and records the creator's challenge without silently reclassifying the content.

Milestone progress is tracked in [docs/development-history.md](docs/development-history.md).

## API Surface
### `POST /submit`
Request body:
```json
{
  "text": "sample text",
  "creator_id": "user-123"
}
```

Response body:
```json
{
  "content_id": "uuid",
  "status": "classified",
  "attribution": "likely_ai",
  "confidence": 0.81,
  "label": "plain language label",
  "signals": {
    "llm_score": 0.84,
    "llm_reason": "short explanation",
    "stylometric_score": 0.75,
    "stylometric_features": {}
  }
}
```

### `POST /appeal`
Request body:
```json
{
  "content_id": "uuid",
  "creator_reasoning": "I wrote this myself."
}
```

Response body:
```json
{
  "message": "Appeal received and marked for review.",
  "content_id": "uuid",
  "status": "under_review",
  "appeal_reasoning": "I wrote this myself."
}
```

### `GET /log`
Returns the most recent structured audit log entries.

## AI Tool Plan
### M3: Submission endpoint + first signal
- **Spec sections to provide:** `Detection Signals` and `Architecture`
- **What to ask for:** Flask app skeleton with `POST /submit`, plus the Groq-based signal function
- **How to verify:** submit a few texts directly and confirm the route returns `content_id`, attribution, and placeholder or real scores

### M4: Second signal + confidence scoring
- **Spec sections to provide:** `Detection Signals`, `Uncertainty Representation`, and `Architecture`
- **What to ask for:** stylometric feature extractor and score-combination logic
- **How to verify:** compare clearly AI-like, clearly human-like, and borderline inputs to ensure the outputs differ meaningfully

### M5: Production layer
- **Spec sections to provide:** `Transparency Label Design`, `Appeals Workflow`, and `Architecture`
- **What to ask for:** label mapping function, `POST /appeal`, and structured logging
- **How to verify:** confirm all three labels can be reached, appeals update status correctly, and `/log` shows both submission and appeal events
