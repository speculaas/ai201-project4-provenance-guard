# Test Inputs

Use these samples to calibrate confidence scoring. Higher confidence means more likely AI-generated. After submitting each, compare `llm_score`, `stylometric_score`, and the combined `confidence` in the response or audit log.

## Likely AI-Generated (expect high confidence)

```text
Artificial intelligence represents a transformative paradigm shift in modern society.
It is important to note that while the benefits of AI are numerous, it is equally
essential to consider the ethical implications. Furthermore, stakeholders across
various sectors must collaborate to ensure responsible deployment.
```

## Likely Human-Written (expect low confidence)

```text
ok so i finally tried that new ramen place downtown and honestly?
underwhelming. the broth was fine but they put WAY too much sodium in it and
i was thirsty for like three hours after. my friend got the spicy version and
said it was better. probably won't go back unless someone drags me there
```

## Uncertain / Borderline: Formal Human Writing

May score mid-high on stylometrics because formal prose looks uniform:

```text
The relationship between monetary policy and asset price inflation has been
extensively studied in the literature. Central banks face a fundamental tension
between their mandate for price stability and the unintended consequences of
prolonged low interest rates on equity and real estate valuations.
```

## Uncertain / Borderline: Lightly Edited AI Output

Should ideally score mid-range:

```text
I've been thinking a lot about remote work lately. There are genuine tradeoffs —
flexibility and no commute on one side, isolation and blurred work-life boundaries
on the other. Studies show productivity varies widely by individual and role type.
```

## Very Short Text (stylometric fallback)

Too short for stable stylometric analysis; expect neutral heuristic score (`0.5`):

```text
Sunset was nice today.
```

## Polished Formal Human Writing (false-positive risk)

Non-native or highly edited human writing that may trigger the LLM signal:

```text
The relationship between economic development and environmental sustainability
requires careful consideration of trade-offs. While industrial growth has lifted
millions from poverty, it has also placed unprecedented pressure on natural
resources and ecosystems worldwide.
```

## Poetry / Repetition (stylometric false-positive risk)

Deliberate repetition and sparse punctuation can look statistically uniform:

```text
rain on the roof
rain on the roof
rain on the roof
and i am still here
waiting
```

## What to Look For

| Category | Expected attribution | Notes |
|----------|---------------------|-------|
| Clearly AI | `likely_ai` | confidence ≥ 0.75 |
| Clearly human | `likely_human` | confidence ≤ 0.35 |
| Borderline | `uncertain` | confidence 0.36–0.74 |
| Very short | varies | stylometric falls back to 0.5 |
| Formal human | often `uncertain` | LLM may over-flag |
| Poetry | often `uncertain` or `likely_ai` | stylometric may over-flag |

If scores do not match intuition, print both signal scores separately to see which signal is misbehaving.
