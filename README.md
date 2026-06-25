# Provenance Guard

Starter implementation for AI201 Project 4. This repo gives you a clean baseline for the required backend flow:

- `POST /submit` accepts text content for attribution analysis
- two detection signals produce AI-likelihood evidence
- confidence scoring maps that evidence to `likely_ai`, `likely_human`, or `uncertain`
- transparency labels translate the result into reader-facing text
- `POST /appeal` lets creators contest a decision
- `GET /log` exposes structured audit entries for documentation and grading

## Project Structure
- `app.py`: Flask routes
- `detector.py`: Groq + stylometric signals
- `scoring.py`: combined confidence score and attribution bucket
- `labels.py`: transparency label text
- `audit.py`: stored submissions and audit logging
- `planning.md`: architecture and design decisions

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add your Groq API key to `.env`:

```bash
GROQ_API_KEY=your_key_here
```

Run the API:

```bash
python app.py
```

## Example Requests
Submit text:

```bash
curl -s -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "The sun dropped behind the houses and the whole block went gold for a minute.", "creator_id": "test-user-1"}'
```

Appeal a decision:

```bash
curl -s -X POST http://localhost:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "PASTE_ID_HERE", "creator_reasoning": "I wrote this from personal experience."}'
```

View the audit log:

```bash
curl -s http://localhost:5000/log
```

## Current Design Choices
This starter uses:
- Groq as the first signal
- stylometric heuristics as the second signal
- a conservative weighted average (`0.65` LLM, `0.35` stylometric)
- a wide uncertain band to reduce false positives against human writers

## Transparency Label Text
Your final README needs the exact wording of all three label variants. This starter currently uses:

| Variant | Exact text |
|---|---|
| High-confidence AI | This post was flagged as likely AI-generated. Our system saw multiple signals that matched machine-generated writing patterns, so readers should treat authorship as likely assisted or produced by AI. |
| High-confidence human | This post appears likely human-written. Our system found enough variation and human-like writing signals to avoid flagging it as AI-generated, but this is still a probabilistic judgment. |
| Uncertain | Our system found mixed evidence and cannot confidently say whether this post was human-written or AI-generated. Readers should treat the attribution as unresolved rather than definitive. |

## What You Still Need To Do
- run the app and calibrate the score thresholds with real test inputs
- generate at least 3 audit log entries and at least 1 appeal entry
- document your rate-limit reasoning in more detail
- expand this README with the final rubric sections
- optionally adjust the heuristics if your sample outputs do not match intuition
