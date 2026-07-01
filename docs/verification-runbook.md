# Verification Runbook

Use this checklist to run the app, calibrate scoring, and collect evidence for your final README. Work in **two terminals**.

All test output is saved under `evidence/logs/` so you can paste into README later (or ask Cursor to do it from those files).

---

## Before you start

**Terminal 1 — start the server (leave running):**

```bash
cd /Users/watney/git/zimmnotes/chat/codepath/ai201/m1/w4/ai201-project4-provenance-guard
source .venv/bin/activate
cp .env.example .env   # only first time
# edit .env: GROQ_API_KEY=...  (FLASK_HOST and FLASK_PORT are optional)
python app.py
```

The server binds to **`0.0.0.0`** by default (all interfaces), not just localhost. You should see:

```text
Provenance Guard listening on http://0.0.0.0:5000
```

**Terminal 2 — set base URL and log directory:**

```bash
cd /Users/watney/git/zimmnotes/chat/codepath/ai201/m1/w4/ai201-project4-provenance-guard

# Same machine:
export BASE_URL="http://localhost:5000"

# From another device on your LAN, use your Mac's IP instead:
# export BASE_URL="http://192.168.1.XXX:5000"

export LOG_DIR="evidence/logs"
mkdir -p "$LOG_DIR"

# Optional: one combined session log with timestamps
export SESSION_LOG="$LOG_DIR/session.log"
echo "=== Verification run started $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" >> "$SESSION_LOG"
```

**Helper — run curl, save raw JSON, pretty-print, append to session log:**

```bash
run_test() {
  local name="$1"
  shift
  echo "=== $name $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee -a "$SESSION_LOG"
  curl -s "$@" | tee "$LOG_DIR/${name}.json" | python3 -m json.tool | tee -a "$SESSION_LOG"
  echo | tee -a "$SESSION_LOG"
}
```

**Tips:**
- Always use `http://` (with `//`).
- Raw JSON files in `evidence/logs/` are the source of truth for README evidence.
- `evidence/` is gitignored — keep files locally.

---

## 1. Run and verify the app (~30–60 min)

### 1a. Health check

```bash
run_test "01_health" "$BASE_URL/"
```

**Verify:** JSON lists `POST /submit`, `POST /appeal`, `GET /log`.

**Saved to:** `evidence/logs/01_health.json`

---

### 1b. Basic submit — returns required fields

```bash
run_test "02_submit_basic" -X POST "$BASE_URL/submit" \
  -H "Content-Type: application/json" \
  -d '{"text": "The sun dipped below the horizon, painting the sky in hues of amber and rose.", "creator_id": "test-user-1"}'
```

**Verify response includes:**
- [ ] `content_id`
- [ ] `attribution` (`likely_ai`, `likely_human`, or `uncertain`)
- [ ] `confidence` (number 0.0–1.0)
- [ ] `label` (plain-language text)
- [ ] `signals.llm_score` and `signals.stylometric_score`

**Saved to:** `evidence/logs/02_submit_basic.json`

**Save `content_id` for appeal test:**

```bash
export CONTENT_ID=$(python3 -c "import json; print(json.load(open('$LOG_DIR/02_submit_basic.json'))['content_id'])")
echo "$CONTENT_ID" | tee "$LOG_DIR/content_id_for_appeal.txt"
```

---

### 1c. All 3 label variants reachable

Submit each sample. Check `attribution` in the response.

**Target A — likely AI** (expect `attribution: likely_ai`, confidence ≥ 0.75):

```bash
run_test "03_submit_likely_ai" -X POST "$BASE_URL/submit" \
  -H "Content-Type: application/json" \
  -d '{"text": "Artificial intelligence represents a transformative paradigm shift in modern society. It is important to note that while the benefits of AI are numerous, it is equally essential to consider the ethical implications. Furthermore, stakeholders across various sectors must collaborate to ensure responsible deployment.", "creator_id": "test-ai"}'
```

**Target B — likely human** (expect `attribution: likely_human`, confidence ≤ 0.35):

```bash
run_test "04_submit_likely_human" -X POST "$BASE_URL/submit" \
  -H "Content-Type: application/json" \
  -d '{"text": "ok so i finally tried that new ramen place downtown and honestly? underwhelming. the broth was fine but they put WAY too much sodium in it and i was thirsty for like three hours after. my friend got the spicy version and said it was better. probably won'\''t go back unless someone drags me there", "creator_id": "test-human"}'
```

**Target C — uncertain** (expect `attribution: uncertain`, confidence 0.36–0.74):

```bash
run_test "05_submit_uncertain" -X POST "$BASE_URL/submit" \
  -H "Content-Type: application/json" \
  -d '{"text": "The relationship between monetary policy and asset price inflation has been extensively studied in the literature. Central banks face a fundamental tension between their mandate for price stability and the unintended consequences of prolonged low interest rates on equity and real estate valuations.", "creator_id": "test-borderline"}'
```

If borderline text does not land in `uncertain`, also try:

```bash
run_test "05b_submit_uncertain_alt" -X POST "$BASE_URL/submit" \
  -H "Content-Type: application/json" \
  -d '{"text": "I'\''ve been thinking a lot about remote work lately. There are genuine tradeoffs — flexibility and no commute on one side, isolation and blurred work-life boundaries on the other. Studies show productivity varies widely by individual and role type.", "creator_id": "test-borderline-2"}'
```

**Verify checklist:**
- [ ] Got `likely_ai` at least once
- [ ] Got `likely_human` at least once
- [ ] Got `uncertain` at least once
- [ ] `label` text changes (not identical across all three)

**Saved to:** `03_submit_likely_ai.json`, `04_submit_likely_human.json`, `05_submit_uncertain.json`

---

### 1d. Appeal — status becomes `under_review`

```bash
run_test "06_appeal" -X POST "$BASE_URL/appeal" \
  -H "Content-Type: application/json" \
  -d "{\"content_id\": \"$CONTENT_ID\", \"creator_reasoning\": \"I wrote this myself from personal experience. I am a non-native English speaker and my writing style may appear more formal than typical.\"}"
```

**Verify:**
- [ ] `"status": "under_review"`
- [ ] `appeal_reasoning` echoed back
- [ ] `"message": "Appeal received and marked for review."`

**Saved to:** `evidence/logs/06_appeal.json`

---

### 1e. Audit log — submissions + appeal

```bash
run_test "07_audit_log" "$BASE_URL/log"
```

**Verify:**
- [ ] At least 3 entries with `"event_type": "submission"`
- [ ] At least 1 entry with `"event_type": "appeal"`
- [ ] Each submission entry has: `content_id`, `attribution`, `confidence`, `llm_score`, `stylometric_score`
- [ ] Appeal entry has: `status: under_review`, `appeal_reasoning`

**Saved to:** `evidence/logs/07_audit_log.json` → **paste into README**

---

### 1f. Rate limit — 429 after 10th request

**Wait ~1 minute** after earlier submits, or restart the server, so you start fresh.

```bash
echo "=== rate limit test $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee "$LOG_DIR/08_rate_limit.txt"
for i in $(seq 1 12); do
  curl -s -o /dev/null -w "request $i: %{http_code}\n" -X POST "$BASE_URL/submit" \
    -H "Content-Type: application/json" \
    -d '{"text": "Rate limit test only.", "creator_id": "ratelimit-test"}' \
    | tee -a "$LOG_DIR/08_rate_limit.txt"
done
cat "$LOG_DIR/08_rate_limit.txt" >> "$SESSION_LOG"
```

**Verify:**
- [ ] Requests 1–10 → `200`
- [ ] Requests 11–12 → `429`

**Saved to:** `evidence/logs/08_rate_limit.txt` → **paste into README**

---

## 2. Calibrate confidence scoring (~30 min)

Goal: confirm scores **vary meaningfully** across clearly different inputs. If they don't, tune `scoring.py` weights/thresholds and re-test.

### 2a. Run all four spec test cases

**Clearly AI:**

```bash
run_test "09_calibrate_ai" -X POST "$BASE_URL/submit" \
  -H "Content-Type: application/json" \
  -d '{"text": "Artificial intelligence represents a transformative paradigm shift in modern society. It is important to note that while the benefits of AI are numerous, it is equally essential to consider the ethical implications. Furthermore, stakeholders across various sectors must collaborate to ensure responsible deployment.", "creator_id": "calibrate-ai"}'
```

**Clearly human:**

```bash
run_test "10_calibrate_human" -X POST "$BASE_URL/submit" \
  -H "Content-Type: application/json" \
  -d '{"text": "ok so i finally tried that new ramen place downtown and honestly? underwhelming. the broth was fine but they put WAY too much sodium in it and i was thirsty for like three hours after.", "creator_id": "calibrate-human"}'
```

**Borderline — formal human:**

```bash
run_test "11_calibrate_formal" -X POST "$BASE_URL/submit" \
  -H "Content-Type: application/json" \
  -d '{"text": "The relationship between monetary policy and asset price inflation has been extensively studied in the literature. Central banks face a fundamental tension between their mandate for price stability and the unintended consequences of prolonged low interest rates on equity and real estate valuations.", "creator_id": "calibrate-formal"}'
```

**Borderline — lightly edited AI:**

```bash
run_test "12_calibrate_edited_ai" -X POST "$BASE_URL/submit" \
  -H "Content-Type: application/json" \
  -d '{"text": "I'\''ve been thinking a lot about remote work lately. There are genuine tradeoffs — flexibility and no commute on one side, isolation and blurred work-life boundaries on the other. Studies show productivity varies widely by individual and role type.", "creator_id": "calibrate-edited-ai"}'
```

### 2b. Fill in this calibration table

| Test case | attribution | confidence | llm_score | stylometric_score | Makes sense? |
|-----------|-------------|------------|-----------|-------------------|--------------|
| Clearly AI | | | | | |
| Clearly human | | | | | |
| Formal human | | | | | |
| Edited AI | | | | | |

Copy values from `09_calibrate_ai.json` through `12_calibrate_edited_ai.json`.

**Pass criteria:**
- [ ] AI sample scores **noticeably higher** than human sample
- [ ] Borderline cases land in `uncertain` or mid-range confidence (not same as extremes)
- [ ] A 0.51 and a 0.95 would produce **different labels** (check thresholds in `scoring.py`)

**If scores look wrong:** note which signal is off (`llm_score` vs `stylometric_score`) before changing code.

**Record:** Pick **two contrasting examples** for README — see section 3.

---

## 3. Collect grading evidence (~20 min)

Paste into final `README.md` using files from `evidence/logs/`.

### 3a. Confidence scoring — two examples (required)

| README section | Source file |
|----------------|-------------|
| High-confidence example | `03_submit_likely_ai.json` or `09_calibrate_ai.json` |
| Lower-confidence example | `05_submit_uncertain.json` or `10_calibrate_human.json` |

Template:

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

---

### 3b. Audit log sample — 3+ entries (required)

| README section | Source file |
|----------------|-------------|
| Audit log evidence | `07_audit_log.json` |

- [ ] At least 2 `submission` events
- [ ] At least 1 `appeal` event

---

### 3c. Rate limiting (required)

| README section | Source file |
|----------------|-------------|
| Rate-limit output | `08_rate_limit.txt` |

Add reasoning, e.g.:

> Limits: `10 per minute; 100 per day` on `POST /submit`.
> A typical creator submits a few pieces per session; 10/min prevents scripted flooding while allowing normal use.

---

### 3d. Appeal workflow (required)

| README section | Source file |
|----------------|-------------|
| Appeal response | `06_appeal.json` |

---

### 3e. Transparency labels (required)

Already in README table — confirm exact text matches what API returns in `03_`, `04_`, `05_` submit files.

---

### 3f. Still to write in README (M6)

- [ ] **Detection signals** — why Groq + stylometrics, what each misses
- [ ] **Known limitations** — one specific content type your system gets wrong
- [ ] **Spec reflection** — one way spec helped, one divergence
- [ ] **AI usage** — 2 specific instances (what you asked, what you changed)
- [ ] **Portfolio walkthrough video** — record separately

**Later:** ask Cursor to read `evidence/logs/` and draft README sections from the saved files.

---

## Quick troubleshooting

| Problem | Fix |
|---------|-----|
| `Expecting value: line 1 column 1` | Use `http://` not `http:`; ensure server is running |
| `Connection refused` | Run `python app.py` in Terminal 1 |
| Can't connect from phone/another PC | Use `BASE_URL=http://YOUR_LAN_IP:5000`; server must bind `0.0.0.0` (default) |
| macOS firewall blocks LAN access | System Settings → Network → Firewall → allow Python |
| All scores ~0.5 | Set `GROQ_API_KEY` in `.env` and restart server |
| Can't reach `uncertain` | Try borderline texts; widen middle band in `scoring.py` if needed |
| Rate limit test all 429 | Wait 1 minute or restart server |

---

## Files you should have when done

```
evidence/logs/
├── session.log                  # combined timestamped log (optional)
├── content_id_for_appeal.txt
├── 01_health.json
├── 02_submit_basic.json
├── 03_submit_likely_ai.json
├── 04_submit_likely_human.json
├── 05_submit_uncertain.json
├── 06_appeal.json
├── 07_audit_log.json            # → README audit log section
├── 08_rate_limit.txt            # → README rate limit section
├── 09_calibrate_ai.json         # → README confidence example (high)
├── 10_calibrate_human.json      # → README confidence example (low)
├── 11_calibrate_formal.json
└── 12_calibrate_edited_ai.json
```

The `evidence/` folder is gitignored. **Graders need the content in README** — the log files are your working copies until you paste or ask Cursor to draft README sections from them.
