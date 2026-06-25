LABELS = {
    "likely_ai": (
        "High-confidence AI label: This post was flagged as likely AI-generated. "
        "Our system saw multiple signals that matched machine-generated writing "
        "patterns, so readers should treat authorship as likely assisted or produced by AI."
    ),
    "likely_human": (
        "High-confidence human label: This post appears likely human-written. "
        "Our system found enough variation and human-like writing signals to avoid "
        "flagging it as AI-generated, but this is still a probabilistic judgment."
    ),
    "uncertain": (
        "Uncertain label: Our system found mixed evidence and cannot confidently say "
        "whether this post was human-written or AI-generated. Readers should treat "
        "the attribution as unresolved rather than definitive."
    ),
}


def label_for_attribution(attribution: str) -> str:
    return LABELS.get(attribution, LABELS["uncertain"])
