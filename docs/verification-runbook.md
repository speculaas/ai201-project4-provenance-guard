# Verification Runbook

Use this checklist to run the app, calibrate scoring, and collect evidence for your final README. Work in **two terminals**.

---

## Before you start

**Terminal 1 — start the server (leave running):**

```bash
cd /Users/watney/git/zimmnotes/chat/codepath/ai201/m1/w4/ai201-project4-provenance-guard
source .venv/bin/activate
cp .env.example .env   # only first time
# edit .env and set GROQ_API_KEY=...
python app.py
```

**Terminal 2 — run all tests below.**

**Tip:** Always use `http://localhost:5000` (with `//`). Pipe to `python3 -m json.tool` for readable JSON.

**Optional — save outputs to a folder:**

```bash
mkdir -p evidence
```

---

## 1. Run and verify the app (~30–60 min)

### 1a. Health check

```bash
curl -s http://localhost:5000/ | python3 -m json.tool
```

**Verify:** JSON lists `POST /submit`, `POST /appeal`, `GET /log`.

**Record:** Not required for README (optional screenshot).

---

### 1b. Basic submit — returns required fields

```bash
curl -s -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "The sun dipped below the horizon, painting the sky in hues of amber and rose.", "creator_id": "test-user-1"}' \
  | tee evidence/submit_basic.json | python3 -m json.tool
```

**Verify response includes:**
- [ ] `content_id`
- [ ] `attribution` (`likely_ai`, `likely_human`, or `uncertain`)
- [ ] `confidence` (number 0.0–1.0)
- [ ] `label` (plain-language text)
- [ ] `signals.llm_score` and `signals.stylometric_score`

**Record:** Save `content_id` for appeal test:

```bash
export CONTENT_ID=$(python3 -c "import json; print(json.load(open('evidence/submit_basic.json'))['content_id'])")
echo $CONTENT_ID
```

---

### 1c. All 3 label variants reachable

Submit each sample. Check `attribution` in the response.

**Target A — likely AI** (expect `attribution: likely_ai`, confidence ≥ 0.75):

```bash
curl -s -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "Artificial intelligence represents a transformative paradigm shift in modern society. It is important to note that while the benefits of AI are numerous, it is equally essential to consider the ethical implications. Furthermore, stakeholders across various sectors must collaborate to ensure responsible deployment.", "creator_id": "test-ai"}' \
  | tee evidence/submit_likely_ai.json | python3 -m json.tool
```

**Target B — likely human** (expect `attribution: likely_human`, confidence ≤ 0.35):

```bash
curl -s -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "ok so i finally tried that new ramen place downtown and honestly? underwhelming. the broth was fine but they put WAY too much sodium in it and i was thirsty for like three hours after. my friend got the spicy version and said it was better. probably won'\''t go back unless someone drags me there", "creator_id": "test-human"}' \
  | tee evidence/submit_likely_human.json | python3 -m json.tool
```

**Target C — uncertain** (expect `attribution: uncertain`, confidence 0.36–0.74):

```bash
curl -s -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "The relationship between monetary policy and asset price inflation has been extensively studied in the literature. Central banks face a fundamental tension between their mandate for price stability and the unintended consequences of prolonged low interest rates on equity and real estate valuations.", "creator_id": "test-borderline"}' \
  | tee evidence/submit_uncertain.json | python3 -m json.tool
```

If borderline text does not land in `uncertain`, also try:

```bash
curl -s -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "I'\''ve been thinking a lot about remote work lately. There are genuine tradeoffs — flexibility and no commute on one side, isolation and blurred work-life boundaries on the other. Studies show productivity varies widely by individual and role type.", "creator_id": "test-borderline-2"}' \
  | tee evidence/submit_uncertain_alt.json | python3 -m json.tool
```

**Verify checklist:**
- [ ] Got `likely_ai` at least once
- [ ] Got `likely_human` at least once
- [ ] Got `uncertain` at least once
- [ ] `label` text changes (not identical across all three)

**Record:** Keep the three JSON files (or note attribution + confidence for each).

---

### 1d. Appeal — status becomes `under_review`

```bash
curl -s -X POST http://localhost:5000/appeal \
  -H "Content-Type: application/json" \
  -d "{\"content_id\": \"$CONTENT_ID\", \"creator_reasoning\": \"I wrote this myself from personal experience. I am a non-native English speaker and my writing style may appear more formal than typical.\"}" \
  | tee evidence/appeal_response.json | python3 -m json.tool
```

**Verify:**
- [ ] `"status": "under_review"`
- [ ] `appeal_reasoning` echoed back
- [ ] `"message": "Appeal received and marked for review."`

**Record:** Save `evidence/appeal_response.json`.

---

### 1e. Audit log — submissions + appeal

```bash
curl -s http://localhost:5000/log | tee evidence/audit_log.json | python3 -m json.tool
```

**Verify:**
- [ ] At least 3 entries with `"event_type": "submission"`
- [ ] At least 1 entry with `"event_type": "appeal"`
- [ ] Each submission entry has: `content_id`, `attribution`, `confidence`, `llm_score`, `stylometric_score`
- [ ] Appeal entry has: `status: under_review`, `appeal_reasoning`

**Record:** Save full log output for README (trim to 3–4 representative entries when pasting).

---

### 1f. Rate limit — 429 after 10th request

**Wait ~1 minute** after earlier submits, or restart the server, so you start fresh.

```bash
for i in $(seq 1 12); do
  curl -s -o /dev/null -w "request $i: %{http_code}\n" -X POST http://localhost:5000/submit \
    -H "Content-Type: application/json" \
    -d '{"text": "Rate limit test only.", "creator_id": "ratelimit-test"}'
done | tee evidence/rate_limit_output.txt
```

**Verify:**
- [ ] Requests 1–10 → `200`
- [ ] Requests 11–12 → `429`

**Record:** Paste `evidence/rate_limit_output.txt` into README.

---

## 2. Calibrate confidence scoring (~30 min)

Goal: confirm scores **vary meaningfully** across clearly different inputs. If they don't, tune `scoring.py` weights/thresholds and re-test.

### 2a. Run all four spec test cases

**Clearly AI:**

```bash
curl -s -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "Artificial intelligence represents a transformative paradigm shift in modern society. It is important to note that while the benefits of AI are numerous, it is equally essential to consider the ethical implications. Furthermore, stakeholders across various sectors must collaborate to ensure responsible deployment.", "creator_id": "calibrate-ai"}' \
  | python3 -m json.tool
```

**Clearly human:**

```bash
curl -s -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "ok so i finally tried that new ramen place downtown and honestly? underwhelming. the broth was fine but they put WAY too much sodium in it and i was thirsty for like three hours after.", "creator_id": "calibrate-human"}' \
  | python3 -m json.tool
```

**Borderline — formal human:**

```bash
curl -s -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "The relationship between monetary policy and asset price inflation has been extensively studied in the literature. Central banks face a fundamental tension between their mandate for price stability and the unintended consequences of prolonged low interest rates on equity and real estate valuations.", "creator_id": "calibrate-formal"}' \
  | python3 -m json.tool
```

**Borderline — lightly edited AI:**

```bash
curl -s -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "I'\''ve been thinking a lot about remote work lately. There are genuine tradeoffs — flexibility and no commute on one side, isolation and blurred work-life boundaries on the other. Studies show productivity varies widely by individual and role type.", "creator_id": "calibrate-edited-ai"}' \
  | python3 -m json.tool
```

### 2b. Fill in this calibration table

| Test case | attribution | confidence | llm_score | stylometric_score | Makes sense? |
|-----------|-------------|------------|-----------|-------------------|--------------|
| Clearly AI | | | | | |
| Clearly human | | | | | |
| Formal human | | | | | |
| Edited AI | | | | | |

**Pass criteria:**
- [ ] AI sample scores **noticeably higher** than human sample
- [ ] Borderline cases land in `uncertain` or mid-range confidence (not same as extremes)
- [ ] A 0.51 and a 0.95 would produce **different labels** (check thresholds in `scoring.py`)

**If scores look wrong:** note which signal is off (`llm_score` vs `stylometric_score`) before changing code.

**Record:** Pick **two contrasting examples** (one high-confidence, one lower) for README — see section 3.

---

## 3. Collect grading evidence (~20 min)

Paste these into your final `README.md`. Use real output from your runs above.

### 3a. Confidence scoring — two examples (required)

Pick one high-confidence case and one lower-confidence case. Template:

```markdown
### Example 1 — high-confidence AI
- **Input:** (first ~50 chars of text…)
- **attribution:** likely_ai
- **confidence:** 0.XX
- **llm_score:** 0.XX
- **stylometric_score:** 0.XX

### Example 2 — lower-confidence / uncertain
- **Input:** (first ~50 chars of text…)
- **attribution:** uncertain
- **confidence:** 0.XX
- **llm_score:** 0.XX
- **stylometric_score:** 0.XX
```

Source files: `evidence/submit_likely_ai.json` + `evidence/submit_uncertain.json` (or similar).

---

### 3b. Audit log sample — 3+ entries (required)

Paste trimmed JSON from `evidence/audit_log.json`:

- [ ] At least 2 `submission` events
- [ ] At least 1 `appeal` event

---

### 3c. Rate limiting (required)

Paste from `evidence/rate_limit_output.txt` and add reasoning, e.g.:

> Limits: `10 per minute; 100 per day` on `POST /submit`.
> A typical creator submits a few pieces per session; 10/min prevents scripted flooding while allowing normal use.

---

### 3d. Transparency labels (required)

Already in README table — confirm exact text matches what API returns for each bucket.

---

### 3e. Still to write in README (M6)

- [ ] **Detection signals** — why Groq + stylometrics, what each misses
- [ ] **Known limitations** — one specific content type your system gets wrong
- [ ] **Spec reflection** — one way spec helped, one divergence
- [ ] **AI usage** — 2 specific instances (what you asked, what you changed)
- [ ] **Portfolio walkthrough video** — record separately

---

## Quick troubleshooting

| Problem | Fix |
|---------|-----|
| `Expecting value: line 1 column 1` | Use `http://` not `http:`; ensure server is running |
| `Connection refused` | Run `python app.py` in Terminal 1 |
| All scores ~0.5 | Set `GROQ_API_KEY` in `.env` and restart server |
| Can't reach `uncertain` | Try borderline texts; widen middle band in `scoring.py` if needed |
| Rate limit test all 429 | Wait 1 minute or restart server |

---

## Files you should have when done

```
evidence/
├── submit_basic.json
├── submit_likely_ai.json
├── submit_likely_human.json
├── submit_uncertain.json
├── appeal_response.json
├── audit_log.json
└── rate_limit_output.txt
```

The `evidence/` folder is for your local notes — add it to `.gitignore` if you don't want to commit test artifacts. **What graders need is the content pasted into README**, not necessarily the folder itself.
