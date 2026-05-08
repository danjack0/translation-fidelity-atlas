"""
Single-pivot back-translation experiment.

This is the headline experiment of the project. For every (translator,
target language, content domain) cell we:

1. Translate ``en`` → target language
2. Translate target language → ``en``
3. Score the round-tripped text against the original.

Languages are translated in parallel; sentences within a language are
translated sequentially, sharing the disk-backed cache so re-running the
experiment after adding a new translator or a new domain does not pay for
the cells that have already been done.
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

from ..config import DOMAINS, METRICS
from ..scoring import all_metrics
from ..translators import Translator, load_cache, save_cache
from ..translators.cache import cache_key

log = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Cached translation primitives                                               #
# --------------------------------------------------------------------------- #

def _translate_one(
    text: str,
    src: str,
    tgt: str,
    translator: Translator,
    cache: dict[str, str],
    retries: int = 3,
) -> str:
    """Translate one string with cache check + exponential-backoff retry."""
    key = cache_key(text, src, tgt, translator.name)
    if key in cache:
        return cache[key]

    for attempt in range(retries):
        try:
            result = translator.translate(text, src, tgt)
            cache[key] = result
            return result
        except Exception as exc:                                   # noqa: BLE001
            wait = 0.5 * (2 ** attempt)
            log.warning(
                "[%s] %s→%s attempt %d/%d failed: %s. Retrying in %.1fs",
                translator.name, src, tgt, attempt + 1, retries, exc, wait,
            )
            time.sleep(wait)

    log.error("[%s] %s→%s permanently failed for: %r",
              translator.name, src, tgt, text)
    return text  # preserve corpus alignment


def _translate_corpus(
    sentences: list[str],
    src: str,
    tgt: str,
    translator: Translator,
    cache: dict[str, str],
    delay: float = 0.0,
) -> list[str]:
    """Translate every sentence sequentially, sharing the cache."""
    out = []
    for s in sentences:
        out.append(_translate_one(s, src, tgt, translator, cache))
        time.sleep(delay)
    return out


# --------------------------------------------------------------------------- #
# Back-translation                                                            #
# --------------------------------------------------------------------------- #

def back_translate(
    sentences: list[str],
    target_langs: list[str],
    translator: Translator,
    cache: dict[str, str],
    source_lang: str = "en",
    max_workers: int = 4,
) -> dict[str, dict[str, list[str]]]:
    """
    Forward + reverse translate ``sentences`` through every target language.

    Returns
    -------
    ``{lang: {"forward": [...], "back": [...]}}``
    """
    results: dict[str, dict[str, list[str]]] = {}

    def _do_lang(lang: str) -> tuple[str, dict[str, list[str]]]:
        log.info("  [%s] %s → %s", translator.name, source_lang, lang)
        forward = _translate_corpus(sentences, source_lang, lang, translator, cache)
        time.sleep(0.1)
        log.info("  [%s] %s → %s", translator.name, lang, source_lang)
        back = _translate_corpus(forward, lang, source_lang, translator, cache)
        return lang, {"forward": forward, "back": back}

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_do_lang, lang): lang for lang in target_langs}
        for fut in as_completed(futures):
            lang, payload = fut.result()
            results[lang] = payload

    return results


# --------------------------------------------------------------------------- #
# Full experiment                                                             #
# --------------------------------------------------------------------------- #

def run_experiment(
    domain_corpora: dict[str, list[str]],
    families: dict[str, list[str]],
    translator: Translator,
    cache_path: str | Path,
    output_dir: str | Path,
    max_workers: int = 4,
) -> pd.DataFrame:
    """
    Run the full back-translation experiment for one translator.

    For every family × language × domain, translates en → lang → en and scores
    the result on all four metrics. Writes per-family checkpoint CSVs to
    ``output_dir/per_family/`` and a combined long-format CSV at
    ``output_dir/back_translation_long.csv``.

    Returns the long-format DataFrame.
    """
    output_dir = Path(output_dir)
    (output_dir / "per_family").mkdir(parents=True, exist_ok=True)

    cache = load_cache(cache_path)
    long_records: list[dict] = []

    for family, langs in families.items():
        log.info("=" * 60)
        log.info("Family: %s   (%d languages)", family, len(langs))
        log.info("=" * 60)

        for domain, corpus in domain_corpora.items():
            log.info("  Domain: %s", domain)
            bt = back_translate(
                corpus, langs, translator, cache,
                max_workers=max_workers,
            )
            save_cache(cache, cache_path)  # checkpoint after every domain

            for lang in langs:
                scores = all_metrics(corpus, bt[lang]["back"])
                long_records.append({
                    "translator": translator.name,
                    "family":     family,
                    "language":   lang,
                    "domain":     domain,
                    **scores,
                })

        # per-family wide-format checkpoint
        fam_df = _records_to_wide(
            [r for r in long_records if r["family"] == family]
        )
        fam_df.to_csv(output_dir / "per_family" / f"{family}.csv", index=False)
        log.info("  → checkpoint: per_family/%s.csv", family)

    save_cache(cache, cache_path)

    long_df = pd.DataFrame(long_records)
    long_df.to_csv(output_dir / "back_translation_long.csv", index=False)
    _records_to_wide(long_records).to_csv(
        output_dir / "back_translation_wide.csv", index=False
    )
    log.info("Done. %d (lang × domain) cells written.", len(long_df))
    return long_df


def _records_to_wide(records: list[dict]) -> pd.DataFrame:
    """Pivot long records into wide format with topical (across-domain) means."""
    long_df = pd.DataFrame(records)
    rows: list[dict] = []
    for (translator, family, lang), grp in long_df.groupby(
        ["translator", "family", "language"], sort=False
    ):
        row = {"translator": translator, "family": family, "language": lang}
        for _, r in grp.iterrows():
            d = r["domain"]
            for m in METRICS:
                row[f"{d}_{m}"] = r[m]
        for m in METRICS:
            row[f"topical_{m}"] = grp[m].mean()
        rows.append(row)
    return pd.DataFrame(rows)


def load_corpora(corpus_dir: str | Path) -> dict[str, list[str]]:
    """Load every domain corpus from ``{corpus_dir}/{domain}.txt``."""
    corpus_dir = Path(corpus_dir)
    out: dict[str, list[str]] = {}
    for domain in DOMAINS:
        path = corpus_dir / f"{domain}.txt"
        with path.open("r", encoding="utf-8") as f:
            out[domain] = [ln.rstrip("\n") for ln in f if ln.strip()]
    return out
