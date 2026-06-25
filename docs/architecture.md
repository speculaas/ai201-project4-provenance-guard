# Provenance Guard Architecture

This document is the visual architecture reference for the project. The ASCII flow in `planning.md` is the planning baseline; these Mermaid diagrams are the maintained dev-history view of how the system is wired.

## System Flowchart

Submission path from client request to JSON response:

```mermaid
flowchart TD
    A[Client submits text] --> B[POST /submit in app.py]
    B --> C[Validate JSON body]
    C --> D[Groq LLM authorship signal]
    C --> E[Stylometric heuristic signal]
    D --> F[Combine signal scores in scoring.py]
    E --> F
    F --> G{Attribution bucket}
    G -->|0.00 - 0.35| H[likely_human]
    G -->|0.36 - 0.74| I[uncertain]
    G -->|0.75 - 1.00| J[likely_ai]
    H --> K[Generate transparency label]
    I --> K
    J --> K
    K --> L[Save submission record]
    L --> M[Append audit log entry]
    M --> N[Return JSON response]
```

## Component Responsibilities

Module boundaries and persistence targets:

```mermaid
flowchart LR
    APP["app.py<br/>Flask routes"] --> DETECTOR["detector.py<br/>LLM + stylometric signals"]
    DETECTOR --> SCORING["scoring.py<br/>confidence + attribution"]
    SCORING --> LABELS["labels.py<br/>reader-facing labels"]
    LABELS --> AUDIT["audit.py<br/>submission storage + JSONL audit log"]
    AUDIT --> LOGS["logs/audit.jsonl"]
    AUDIT --> DATA["data/submissions.json"]
```

## Submit Sequence

Request/response behavior for `POST /submit`:

```mermaid
sequenceDiagram
    participant Client
    participant App as app.py
    participant Detector as detector.py
    participant Scoring as scoring.py
    participant Labels as labels.py
    participant Audit as audit.py

    Client->>App: POST /submit text + creator_id
    App->>App: Validate request body
    App->>Detector: Run LLM authorship signal
    Detector-->>App: llm_score + reason
    App->>Detector: Run stylometric signal
    Detector-->>App: stylometric_score + features
    App->>Scoring: Combine scores
    Scoring-->>App: attribution + confidence
    App->>Labels: Get transparency label
    Labels-->>App: label text
    App->>Audit: Save submission record
    App->>Audit: Append submission event
    App-->>Client: JSON response
```

## Appeal Sequence

Request/response behavior for `POST /appeal`:

```mermaid
sequenceDiagram
    participant Client
    participant App as app.py
    participant Audit as audit.py

    Client->>App: POST /appeal content_id + creator_reasoning
    App->>App: Validate request body
    App->>Audit: Look up submission
    Audit-->>App: Existing submission record
    App->>Audit: Mark status under_review
    App->>Audit: Append appeal audit event
    App-->>Client: Appeal confirmation JSON
```

## Design Notes

- **Confidence score** is an AI-likelihood score (higher = more likely AI-generated), not a certainty claim.
- **False-positive bias:** the uncertain band (`0.36`–`0.74`) is intentionally wide so borderline human writing is not over-flagged.
- **Rate limiting** applies only to `POST /submit` (`10 per minute; 100 per day`).
- **Appeals** do not trigger automatic re-classification; they update status and append a second audit event.
