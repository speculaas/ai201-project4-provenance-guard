from typing import Any


def combine_signal_scores(llm_score: float, stylometric_score: float) -> float:
    """
    Higher means "more likely AI-generated."

    The weighting is conservative about false positives:
    - the LLM gets more weight because it evaluates the whole text
    - the stylometric signal acts as an independent structural check
    """
    combined = (llm_score * 0.65) + (stylometric_score * 0.35)
    return round(max(0.0, min(1.0, combined)), 3)


def classify_from_score(score: float) -> str:
    """
    Maps an AI-likelihood score into the three required buckets.

    The middle band is intentionally wide so borderline content is labeled
    as uncertain instead of overclaiming that a human author used AI.
    """
    if score >= 0.75:
        return "likely_ai"
    if score <= 0.35:
        return "likely_human"
    return "uncertain"


def build_decision(llm_signal: dict[str, Any], stylometric_signal: dict[str, Any]) -> dict[str, Any]:
    confidence = combine_signal_scores(llm_signal["score"], stylometric_signal["score"])
    attribution = classify_from_score(confidence)
    return {
        "attribution": attribution,
        "confidence": confidence,
        "signals": {
            "llm": llm_signal,
            "stylometric": stylometric_signal,
        },
    }
