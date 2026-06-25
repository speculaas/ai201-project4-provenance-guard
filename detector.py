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

    prompt = (
        "You are evaluating whether a piece of creative writing looks AI-generated "
        "or human-written. Return JSON only with keys: "
        '"score" (0.0 to 1.0, where higher means more likely AI-generated) and '
        '"reason" (one short sentence). Be cautious about false positives. '
        "Formal writing, second-language writing, and edited human writing can still "
        "be human-written."
    )

    client = Groq(api_key=api_key)

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0.2,
            messages=[
                {"role": "system", "content": prompt},
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

    This starter uses three easy-to-explain heuristics:
    - low sentence-length variance can indicate more uniform writing
    - low punctuation density can indicate cleaner, more standardized prose
    - lower vocabulary diversity can indicate repetitive wording
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
            },
            "reason": "Text is too short for a stable stylometric judgment.",
        }

    sentence_lengths = _sentence_lengths(sentences)
    variance = statistics.pvariance(sentence_lengths) if len(sentence_lengths) > 1 else 0.0
    type_token_ratio = len(set(words)) / len(words)
    punctuation_density = punctuation_count / len(words)

    variance_ai = 1.0 - min(variance / 30.0, 1.0)
    ttr_ai = 1.0 - min(max((type_token_ratio - 0.3) / 0.4, 0.0), 1.0)
    punctuation_ai = 1.0 - min(punctuation_density / 0.12, 1.0)

    score = _clip_score((variance_ai * 0.45) + (ttr_ai * 0.35) + (punctuation_ai * 0.20))

    return {
        "score": score,
        "features": {
            "sentence_length_variance": round(variance, 3),
            "type_token_ratio": round(type_token_ratio, 3),
            "punctuation_density": round(punctuation_density, 3),
        },
        "reason": "Higher scores reflect more uniform structure and lower stylistic variation.",
    }
