"""
Round-trip directional asymmetry: ABA versus BAB.

A round-trip translation can be measured in two ways:

* **ABA** (English-anchored): ``en → tgt → en``, score the back-translated
  English against the original English.
* **BAB** (target-anchored): ``en → tgt → en → tgt``, score the final target
  string against the first ``en → tgt`` output.

If the two systems were perfectly symmetric translation pairs, ABA and BAB
fidelity would be equal. Any divergence is a directional asymmetry — the
model is, e.g., better at ``en → ja`` than at ``ja → en``, so most of the
information loss happens on one side of the round trip rather than being
distributed evenly.

This experiment surfaces the asymmetry by running both protocols on the
same languages and reporting the gap.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from ..scoring.lexical import bleu, cosine, ter
from ..translators import Translator, load_cache, save_cache
from .back_translation import _translate_corpus

log = logging.getLogger(__name__)


def _hop_scores(originals: list[str], candidates: list[str]) -> dict[str, float]:
    return {
        "cosine": cosine(originals, candidates),
        "bleu":   bleu(originals, candidates),
        "ter":    ter(originals, candidates),
    }


def run_round_trip(
    domain_corpora: dict[str, list[str]],
    languages: list[str],
    translator: Translator,
    cache_path: str | Path,
    output_csv: str | Path | None = None,
) -> pd.DataFrame:
    """
    For each language and domain, compute both ABA and BAB scores.

    ABA scores (back-EN) against (original-EN).
    BAB scores (re-translated-TGT) against (first-pass-TGT).

    Returns a long-format DataFrame, optionally also writing it to ``output_csv``.
    """
    cache = load_cache(cache_path)
    records: list[dict] = []

    for lang in languages:
        for domain, originals in domain_corpora.items():
            log.info("[%s | %s | %s] ABA + BAB", translator.name, lang, domain)

            # ABA: en → tgt → en, scored against original en
            forward = _translate_corpus(originals, "en", lang, translator, cache)
            aba_back = _translate_corpus(forward, lang, "en", translator, cache)
            records.append({
                "translator": translator.name,
                "language":   lang,
                "domain":     domain,
                "direction":  "ABA",
                **_hop_scores(originals, aba_back),
            })

            # BAB: tgt → en → tgt, scored against the first-pass tgt
            #
            # We reuse the en obtained on the ABA pass — that is the
            # "intermediate" English that BAB also produces, by definition.
            bab_tgt = _translate_corpus(aba_back, "en", lang, translator, cache)
            records.append({
                "translator": translator.name,
                "language":   lang,
                "domain":     domain,
                "direction":  "BAB",
                **_hop_scores(forward, bab_tgt),
            })

    save_cache(cache, cache_path)
    df = pd.DataFrame(records)
    if output_csv is not None:
        output_csv = Path(output_csv)
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_csv, index=False)
        log.info("Round-trip dataset: %d rows → %s", len(df), output_csv)
    return df
