"""
Central configuration: language families, content domains, metrics, and display
constants. Importing from this module is the only sanctioned way to reference
these values — no string literals scattered through the codebase.

Naming conventions
------------------
* Families  — ``snake_case`` in data, Title Case for display
  (e.g. ``east_asian`` → "East Asian").
* Domains   — full English words (``conversational``, ``idiomatic``).
* Metrics   — ``cosine`` (lexical, spaCy word vectors), ``bleu``, ``ter``,
  ``embedding`` (semantic, sentence-transformer cosine).
"""

from __future__ import annotations

# --------------------------------------------------------------------------- #
# Language families                                                           #
# --------------------------------------------------------------------------- #

LANGUAGE_FAMILIES: dict[str, list[str]] = {
    "romance":        ["it", "es", "fr", "pt", "ro", "ca", "gl"],
    "germanic":       ["de", "nl", "sv", "da", "no", "af", "is"],
    "slavic":         ["ru", "pl", "cs", "uk", "bg", "sr", "hr", "sk", "sl"],
    "semitic":        ["ar", "iw", "mt"],
    "east_asian":     ["zh-CN", "ja", "ko"],
    "south_se_asian": ["hi", "bn", "ur", "ta", "te", "th", "vi", "id", "ms"],
    "turkic":         ["tr", "az", "kk", "uz"],
    "uralic":         ["fi", "et", "hu"],
}

#: Display order for figures, ordered by typological proximity to English.
FAMILY_ORDER: list[str] = [
    "romance", "germanic", "uralic", "slavic",
    "semitic", "east_asian", "south_se_asian", "turkic",
]


def family_display_name(family: str) -> str:
    """Render a snake_case family code as a Title-Case display label."""
    return family.replace("_", " ").title()


# --------------------------------------------------------------------------- #
# Content domains                                                             #
# --------------------------------------------------------------------------- #

DOMAINS: list[str] = [
    "conversational", "cultural", "idiomatic",
    "technical", "legal", "emotional",
]

#: Display order chosen to group register types from formal → informal.
DOMAIN_ORDER: list[str] = [
    "technical", "legal", "cultural",
    "conversational", "emotional", "idiomatic",
]

DOMAIN_FILES: dict[str, str] = {d: f"{d}.txt" for d in DOMAINS}


# --------------------------------------------------------------------------- #
# Metrics                                                                     #
# --------------------------------------------------------------------------- #

METRICS: list[str] = ["cosine", "bleu", "ter", "embedding"]

#: Direction of "better" for each metric.
METRIC_HIGHER_IS_BETTER: dict[str, bool] = {
    "cosine":    True,
    "bleu":      True,
    "ter":       False,
    "embedding": True,
}

METRIC_LABELS: dict[str, str] = {
    "cosine":    "Cosine Similarity (lexical)",
    "bleu":      "BLEU",
    "ter":       "TER",
    "embedding": "Embedding Similarity (semantic)",
}


# --------------------------------------------------------------------------- #
# Telephone-chain experiment                                                  #
# --------------------------------------------------------------------------- #

# One representative language per family, ordered by linguistic distance from
# English. The reverse and random orders are fixed so results are reproducible.
CHAIN_ORDER_LINGUISTIC = ["es", "de", "ru", "ar", "ja"]
CHAIN_ORDER_REVERSE    = ["ja", "ar", "ru", "de", "es"]
CHAIN_ORDER_RANDOM     = ["ru", "es", "ja", "de", "ar"]

CHAIN_ORDERS: dict[str, list[str]] = {
    "linguistic": CHAIN_ORDER_LINGUISTIC,
    "reverse":    CHAIN_ORDER_REVERSE,
    "random":     CHAIN_ORDER_RANDOM,
}


# --------------------------------------------------------------------------- #
# Display palette                                                             #
# --------------------------------------------------------------------------- #

TRANSLATOR_COLORS: dict[str, str] = {
    "google": "#4285F4",
    "nllb":   "#7B1FA2",
}

TRANSLATOR_ORDER: list[str] = ["google", "nllb"]

DOMAIN_COLORS: dict[str, str] = {
    "technical":      "#1565C0",
    "legal":          "#6A1B9A",
    "cultural":       "#00838F",
    "conversational": "#EF6C00",
    "emotional":      "#AD1457",
    "idiomatic":      "#558B2F",
}

CHAIN_ORDER_STYLES: dict[str, dict] = {
    "linguistic": {"linestyle": "-",  "marker": "o"},
    "reverse":    {"linestyle": "--", "marker": "s"},
    "random":     {"linestyle": ":",  "marker": "^"},
}
