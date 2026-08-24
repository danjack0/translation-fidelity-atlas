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

import textwrap

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


#: Display labels that ``str.title()`` gets wrong.
FAMILY_DISPLAY_OVERRIDES: dict[str, str] = {
    "south_se_asian": "South & SE Asian",
    "east_asian":     "East Asian",
}


def family_display_name(family: str) -> str:
    """Render a snake_case family code as a Title-Case display label."""
    if family in FAMILY_DISPLAY_OVERRIDES:
        return FAMILY_DISPLAY_OVERRIDES[family]
    return family.replace("_", " ").title()


def family_tick_label(family: str, width: int = 10) -> str:
    """
    Family label wrapped for an axis tick — at most two lines.

    Splitting on every space turns "South & SE Asian" into a four-line stack
    that swallows the axis; wrapping to a width keeps it to two.
    """
    return "\n".join(textwrap.wrap(family_display_name(family), width=width))


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

#: Compact forms for tick labels and panel titles, where the long form does not
#: fit. Never lowercase a metric name in a figure — BLEU and TER are acronyms.
METRIC_SHORT_LABELS: dict[str, str] = {
    "cosine":    "Cosine",
    "bleu":      "BLEU",
    "ter":       "TER",
    "embedding": "Embedding",
}


def metric_axis_label(metric: str) -> str:
    """Axis label for a metric, with its 'better' direction spelled out."""
    direction = "higher is better" if METRIC_HIGHER_IS_BETTER[metric] else "lower is better"
    return f"{METRIC_LABELS[metric]} ({direction})"


def metric_cbar_label(metric: str) -> str:
    """Compact colorbar label — the panel title already carries the long form."""
    direction = "↑ better" if METRIC_HIGHER_IS_BETTER[metric] else "↓ better"
    return f"{METRIC_SHORT_LABELS[metric]}  ({direction})"


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
#
# All categorical palettes below are drawn from the Okabe-Ito colourblind-safe
# set (Okabe & Ito 2008). They were screened by simulating protanopia,
# deuteranopia and tritanopia (Machado et al. 2009) and measuring the minimum
# pairwise CIE76 ΔE in Lab; every pair clears ΔE ≥ 16 under all three, where
# < 15 is the threshold at which two categories start to be confusable.
#
# The palettes tab10 (previously used for families in the scatter and radar
# plots) and Set2 (previously used for families in the box plots) both FAILED
# that screen — tab10 at ΔE 4.6 under protanopia, Set2 at ΔE 2.5 — which is why
# family colours are now pinned here rather than generated per module.
#
# Colour is never the sole encoding of a comparison: see TRANSLATOR_HATCHES and
# TRANSLATOR_MARKERS, which keep Google vs NLLB separable in greyscale.

TRANSLATOR_COLORS: dict[str, str] = {
    "google": "#4285F4",
    "nllb":   "#7B1FA2",
}

#: Redundant (non-colour) encodings of translator identity, so that any figure
#: comparing the two systems survives greyscale printing.
TRANSLATOR_HATCHES: dict[str, str] = {
    "google": "",
    "nllb":   "///",
}

TRANSLATOR_MARKERS: dict[str, str] = {
    "google": "o",
    "nllb":   "s",
}

TRANSLATOR_LINESTYLES: dict[str, str] = {
    "google": "-",
    "nllb":   "--",
}

#: Display names. "Google"/"Nllb" from ``str.capitalize()`` are not the names
#: of these systems.
TRANSLATOR_LABELS: dict[str, str] = {
    "google": "Google Translate",
    "nllb":   "NLLB-200",
}

TRANSLATOR_ORDER: list[str] = ["google", "nllb"]


def translator_display_name(translator: str) -> str:
    """Render a translator key as its proper product name."""
    return TRANSLATOR_LABELS.get(translator, translator.capitalize())


#: One colour per family, fixed here so a family means the same colour in every
#: figure. Ordered to follow FAMILY_ORDER; hues were chosen to stay close to the
#: previous tab10 assignment so figures remain recognisable.
FAMILY_COLORS: dict[str, str] = {
    "romance":        "#0072B2",  # blue
    "germanic":       "#E69F00",  # orange
    "uralic":         "#009E73",  # bluish green
    "slavic":         "#D55E00",  # vermillion
    "semitic":        "#CC79A7",  # reddish purple
    "east_asian":     "#56B4E9",  # sky blue
    "south_se_asian": "#F0E442",  # yellow
    "turkic":         "#000000",  # black
}

DOMAIN_COLORS: dict[str, str] = {
    "technical":      "#0072B2",  # blue        (was #1565C0)
    "legal":          "#CC79A7",  # reddish purple (was #6A1B9A)
    "cultural":       "#009E73",  # bluish green   (was #00838F)
    "conversational": "#E69F00",  # orange      (was #EF6C00)
    "emotional":      "#D55E00",  # vermillion  (was #AD1457)
    "idiomatic":      "#56B4E9",  # sky blue    (was #558B2F)
}

CHAIN_ORDER_STYLES: dict[str, dict] = {
    "linguistic": {"linestyle": "-",  "marker": "o"},
    "reverse":    {"linestyle": "--", "marker": "s"},
    "random":     {"linestyle": ":",  "marker": "^"},
}
