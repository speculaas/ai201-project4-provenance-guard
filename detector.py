import json
import os
import re
import statistics
from typing import Any

from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:  # pragma: no cover - makes local setup smoother before pip install
    Groq = None

load_dotenv()

MODEL_NAME = "llama-3.3-70b-versatile"
DEFAULT_LLM_SCORE = 0.5

# Common in polished AI/LLM prose; matched case-insensitively as substrings.
AI_BOILERPLATE_PHRASES = (
    "furthermore",
    "moreover",
    "in conclusion",
    "it is important to note",
    "it is equally essential",
    "paradigm shift",
    "stakeholders",
    "responsible deployment",
    "transformative",
    "in today's society",
    "plays a crucial role",
    "delve into",
    "multifaceted",
    "it's worth noting",
    "at the end of the day",
    "myriad",
    "landscape",
    "holistic",
    "leverage",
    "utilize",
    "in order to",
)

LLM_SYSTEM_PROMPT = """You judge whether text looks AI-generated or human-written.
Return JSON only with keys:
- "score": float from 0.0 to 1.0 (higher = more likely AI-generated)
- "reason": one short sentence

Calibration examples:
- Obvious AI boilerplate with generic transitions and no personal voice: 0.85-0.95
- Casual human writing with irregular grammar and specific details: 0.05-0.20
- Polished formal human or edited borderline writing: 0.35-0.60

AI-like signals: "Furthermore," hedged balanced phrasing, vague authority, no first-person specifics.
Human-like signals: personal anecdotes, typos/informality, idiosyncratic phrasing.

Be cautious about false positives for formal or non-native human writing, but do not under-score
obvious template AI prose."""


def _clip_score(value: float) -> float:
    return max(0.0, min(1.0, round(value, 3)))


def _extract_json_object(text: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model output")
    return json.loads(match.group(0))


def llm_authorship_signal(text: str) -> dict[str, Any]:
    """
    Returns a score where 1.0 means "more likely AI-generated."

    If the API key is missing or the API call fails, this returns a neutral score
    so the rest of the pipeline can still be tested locally.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or Groq is None:
        return {
            "score": DEFAULT_LLM_SCORE,
            "reason": "Groq signal unavailable, so a neutral fallback score was used.",
            "source": "fallback",
        }

    client = Groq(api_key=api_key)

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0.2,
            messages=[
                {"role": "system", "content": LLM_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        )
        raw_content = completion.choices[0].message.content or ""
        payload = _extract_json_object(raw_content)
        score = _clip_score(float(payload.get("score", DEFAULT_LLM_SCORE)))
        reason = str(payload.get("reason", "No reason returned by the model.")).strip()
        return {"score": score, "reason": reason, "source": "groq"}
    except Exception as exc:  # pragma: no cover - external API behavior
        return {
            "score": DEFAULT_LLM_SCORE,
            "reason": f"Groq signal failed, so a neutral fallback score was used: {exc}",
            "source": "fallback",
        }


def _boilerplate_score(text: str, sentence_count: int) -> float:
    """Higher when common AI transition/boilerplate phrases appear frequently."""
    lower = text.lower()
    hits = sum(1 for phrase in AI_BOILERPLATE_PHRASES if phrase in lower)
    hits_per_sentence = hits / max(sentence_count, 1)
    return min(hits_per_sentence / 1.5, 1.0)


def _structural_uniformity_score(
    variance: float, type_token_ratio: float, punctuation_density: float
) -> float:
    """Legacy structural heuristics: uniform length, repetitive vocab, sparse punctuation."""
    variance_ai = 1.0 - min(variance / 30.0, 1.0)
    ttr_ai = 1.0 - min(max((type_token_ratio - 0.3) / 0.4, 0.0), 1.0)
    punctuation_ai = 1.0 - min(punctuation_density / 0.12, 1.0)
    return (variance_ai * 0.45) + (ttr_ai * 0.35) + (punctuation_ai * 0.20)


def _sentence_lengths(sentences: list[str]) -> list[int]:
    lengths = []
    for sentence in sentences:
        words = re.findall(r"\b[\w']+\b", sentence)
        if words:
            lengths.append(len(words))
    return lengths


def stylometric_signal(text: str) -> dict[str, Any]:
    """
    Returns a score where 1.0 means "more likely AI-generated."

    Combines two sub-signals:
    - boilerplate phrase density (catches polished template AI prose)
    - structural uniformity (sentence variance, vocabulary diversity, punctuation)
    """
    words = re.findall(r"\b[\w']+\b", text.lower())
    sentences = [part.strip() for part in re.split(r"[.!?]+", text) if part.strip()]
    punctuation_count = len(re.findall(r"[,:;!?-]", text))

    if len(words) < 20 or len(sentences) < 2:
        return {
            "score": 0.5,
            "features": {
                "sentence_length_variance": 0.0,
                "type_token_ratio": 0.0,
                "punctuation_density": 0.0,
                "boilerplate_hits": 0,
                "boilerplate_score": 0.0,
                "structural_uniformity_score": 0.5,
            },
            "reason": "Text is too short for a stable stylometric judgment.",
        }

    sentence_lengths = _sentence_lengths(sentences)
    variance = statistics.pvariance(sentence_lengths) if len(sentence_lengths) > 1 else 0.0
    type_token_ratio = len(set(words)) / len(words)
    punctuation_density = punctuation_count / len(words)

    lower = text.lower()
    boilerplate_hits = sum(1 for phrase in AI_BOILERPLATE_PHRASES if phrase in lower)
    boilerplate = _boilerplate_score(text, len(sentences))
    structural = _structural_uniformity_score(variance, type_token_ratio, punctuation_density)

    # Boilerplate catches formal AI that looks structurally human; structural catches uniform casual AI.
    score = _clip_score((boilerplate * 0.55) + (structural * 0.45))

    return {
        "score": score,
        "features": {
            "sentence_length_variance": round(variance, 3),
            "type_token_ratio": round(type_token_ratio, 3),
            "punctuation_density": round(punctuation_density, 3),
            "boilerplate_hits": boilerplate_hits,
            "boilerplate_score": round(boilerplate, 3),
            "structural_uniformity_score": round(structural, 3),
        },
        "reason": (
            "Higher scores reflect AI boilerplate phrases and/or uniform structure; "
            "formal AI prose can score high on boilerplate even when sentence variance is high."
        ),
    }
