# Provenance Guard

Starter implementation for AI201 Project 4. This repo gives you a clean baseline for the required backend flow:

- `POST /submit` accepts text content for attribution analysis
- two detection signals produce AI-likelihood evidence
- confidence scoring maps that evidence to `likely_ai`, `likely_human`, or `uncertain`
- transparency labels translate the result into reader-facing text
- `POST /appeal` lets creators contest a decision
- `GET /log` exposes structured audit entries for documentation and grading

## Architecture Summary

A text submission flows through two independent detection signals (Groq LLM + stylometric heuristics), gets combined into a confidence score, maps to one of three attribution buckets, and returns a plain-language transparency label. Every decision is logged; creators can appeal via `content_id`.

See [docs/architecture.md](docs/architecture.md) for Mermaid flowcharts and sequence diagrams.

## Project Structure

```
ai201-project4-provenance-guard/
├── app.py              Flask routes
├── detector.py         Groq LLM + stylometric signals
├── scoring.py          confidence scoring + attribution buckets
├── labels.py           transparency label text
├── audit.py            submission storage + JSONL audit log
├── planning.md         design decisions (written before code)
├── docs/
│   ├── architecture.md       Mermaid diagrams
│   ├── api-flow.md           endpoint reference
│   ├── audit-log.md          log schema
│   └── development-history.md milestone log
└── examples/
    ├── sample_requests.md    curl commands
    └── test_inputs.md        calibration test cases
```

## Documentation

| Document | Contents |
|----------|----------|
| [docs/architecture.md](docs/architecture.md) | System flowchart, component diagram, submit/appeal sequence diagrams |
| [docs/api-flow.md](docs/api-flow.md) | Endpoint reference with example request/response JSON |
| [docs/audit-log.md](docs/audit-log.md) | Audit log schema for submission and appeal events |
| [docs/development-history.md](docs/development-history.md) | Milestone log (M1–M6) with goals, files, and verification steps |
| [examples/sample_requests.md](examples/sample_requests.md) | Copy-paste curl commands |
| [examples/test_inputs.md](examples/test_inputs.md) | Test texts for calibrating confidence scoring |

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

By default the server listens on **`0.0.0.0:5000`** (all network interfaces). Use `http://localhost:5000` on the same machine, or `http://YOUR_LAN_IP:5000` from another device. Override with `FLASK_HOST` / `FLASK_PORT` in `.env`.

## Example Requests

See [examples/sample_requests.md](examples/sample_requests.md) for full curl commands including rate-limit testing.

## Current Design Choices
This starter uses:
- Groq as the first signal
- stylometric heuristics as the second signal (structural uniformity + AI boilerplate phrase density)
- a weighted average (`0.80` LLM, `0.20` stylometric; `0.88`/`0.12` when signals disagree sharply)
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
