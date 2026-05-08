"""
Telephone-chain experiment.

Translate a sentence through a chain of intermediate languages, with no
return to English between hops, and score the cumulative fidelity. This
isolates *compounding* error from single-pivot error: each hop's degradation
sits on top of every previous one.

Three orderings are run for every translator:

* ``linguistic`` — typological distance increasing from English
  (``es → de → ru → ar → ja``).
* ``reverse``    — the same chain reversed.
* ``random``     — a fixed random shuffle (seed-frozen for reproducibility).

For each hop we additionally translate back to English purely for scoring,
without continuing the chain from the back-translation. The chain itself
flows from non-English to non-English.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from ..config import CHAIN_ORDERS
from ..scoring.lexical import bleu, cosine, ter
from ..translators import Translator, load_cache, save_cache
from .back_translation import _translate_corpus

log = logging.getLogger(__name__)


def _hop_scores(originals: list[str], candidates: list[str]) -> dict[str, float]:
    """Three primary metrics per hop. Embedding is intentionally excluded
    here — it would dominate runtime and add little signal at hop level."""
    return {
        "cosine": cosine(originals, candidates),
        "bleu":   bleu(originals, candidates),
        "ter":    ter(originals, candidates),
    }


def run_chain(
    domain_corpora: dict[str, list[str]],
    translator: Translator,
    cache_path: str | Path,
    order_name: str = "linguistic",
) -> list[dict]:
    """
    One translator, one chain order, every domain.

    Returns a list of per-hop records:
    ``{translator, order, domain, hop, lang_code, cosine, bleu, ter}``.
    """
    chain = CHAIN_ORDERS[order_name]
    cache = load_cache(cache_path)
    records: list[dict] = []

    for domain, originals in domain_corpora.items():
        log.info("[%s | %s | %s]", translator.name, order_name, domain)

        current_texts = list(originals)
        current_lang  = "en"

        # Hop 0 — perfect baseline
        records.append({
            "translator": translator.name,
            "order":      order_name,
            "domain":     domain,
            "hop":        0,
            "lang_code":  "en",
            "cosine":     1.0,
            "bleu":       100.0,
            "ter":        0.0,
        })

        for hop_idx, target_lang in enumerate(chain, start=1):
            log.info("  hop %d: %s → %s", hop_idx, current_lang, target_lang)
            current_texts = _translate_corpus(
                current_texts, current_lang, target_lang, translator, cache
            )
            current_lang = target_lang

            # Score by detouring to English (does not affect chain state)
            back_en = _translate_corpus(
                current_texts, target_lang, "en", translator, cache
            )
            records.append({
                "translator": translator.name,
                "order":      order_name,
                "domain":     domain,
                "hop":        hop_idx,
                "lang_code":  target_lang,
                **_hop_scores(originals, back_en),
            })

    save_cache(cache, cache_path)
    return records


def run_all_chains(
    domain_corpora: dict[str, list[str]],
    translators: list[Translator],
    cache_path: str | Path,
    output_csv: str | Path,
    orders: list[str] | None = None,
) -> pd.DataFrame:
    """Run every (translator × order) combination and write a tidy CSV."""
    orders = orders or list(CHAIN_ORDERS.keys())
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    all_records: list[dict] = []
    for tr in translators:
        for order in orders:
            log.info("=" * 60)
            log.info("Translator: %s | Order: %s", tr.name, order)
            log.info("=" * 60)
            all_records.extend(
                run_chain(domain_corpora, tr, cache_path, order_name=order)
            )
            # incremental save
            pd.DataFrame(all_records).to_csv(output_csv, index=False)

    df = pd.DataFrame(all_records)
    df.to_csv(output_csv, index=False)
    log.info("Telephone-chain dataset: %d rows → %s", len(df), output_csv)
    return df
