from typing import Any


def combine_signal_scores(llm_score: float, stylometric_score: float) -> float:
    """
    Higher means "more likely AI-generated."

    LLM gets 80% weight because it evaluates semantics and holistic style.
    Stylometric gets 20% as an independent check (structural + boilerplate features).
    When they disagree sharply, lean slightly more on the LLM to avoid structural false negatives
    on polished formal AI prose.
    """
    combined = (llm_score * 0.80) + (stylometric_score * 0.20)
    if abs(llm_score - stylometric_score) > 0.45:
        combined = (llm_score * 0.88) + (stylometric_score * 0.12)
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
    llm_score = llm_signal["score"]
    styl_score = stylometric_signal["score"]
    confidence = combine_signal_scores(llm_score, styl_score)

    # Polished template AI often scores high on boilerplate but conservative on the LLM judge.
    boilerplate = stylometric_signal.get("features", {}).get("boilerplate_score", 0)
    if boilerplate >= 0.85 and llm_score >= 0.55:
        template_blend = round((llm_score * 0.60) + (boilerplate * 0.40), 3)
        confidence = max(confidence, template_blend)

    attribution = classify_from_score(confidence)
    return {
        "attribution": attribution,
        "confidence": confidence,
        "signals": {
            "llm": llm_signal,
            "stylometric": stylometric_signal,
        },
    }
