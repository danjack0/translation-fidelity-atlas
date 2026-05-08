"""
Smoke tests. These verify imports and pure-Python correctness; they don't
hit any translation API or load any large model.

Run: ``pytest`` from the repo root.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from translation_fidelity_atlas.analysis import (
    extreme_cells,
    one_way_anova,
    summary_by,
    variance_decomposition,
)
from translation_fidelity_atlas.config import (
    DOMAINS,
    FAMILY_ORDER,
    LANGUAGE_FAMILIES,
    METRICS,
    family_display_name,
)
from translation_fidelity_atlas.translators.cache import (
    cache_key,
    load_cache,
    save_cache,
)


# --------------------------------------------------------------------------- #
# Config sanity                                                               #
# --------------------------------------------------------------------------- #

def test_family_order_covers_every_family():
    assert set(FAMILY_ORDER) == set(LANGUAGE_FAMILIES.keys())


def test_every_family_has_at_least_three_languages():
    for fam, langs in LANGUAGE_FAMILIES.items():
        assert len(langs) >= 3, f"Family {fam} only has {len(langs)} languages"


def test_no_duplicate_languages_across_families():
    seen: dict[str, str] = {}
    for fam, langs in LANGUAGE_FAMILIES.items():
        for lang in langs:
            assert lang not in seen, f"{lang} in both {seen[lang]} and {fam}"
            seen[lang] = fam


def test_family_display_name_is_titlecase():
    assert family_display_name("east_asian") == "East Asian"
    assert family_display_name("romance") == "Romance"


def test_domains_metrics_constants():
    assert len(DOMAINS) == 6
    assert set(METRICS) == {"cosine", "bleu", "ter", "embedding"}


# --------------------------------------------------------------------------- #
# Cache primitives                                                            #
# --------------------------------------------------------------------------- #

def test_cache_key_is_stable():
    a = cache_key("hello", "en", "fr", "google")
    b = cache_key("hello", "en", "fr", "google")
    assert a == b
    assert len(a) == 32  # md5 hex


def test_cache_key_is_translator_namespaced():
    a = cache_key("hi", "en", "fr", "google")
    b = cache_key("hi", "en", "fr", "nllb")
    assert a != b


def test_cache_roundtrip_uncompressed():
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "cache.json"
        cache = {cache_key("foo", "en", "es", "google"): "comida"}
        save_cache(cache, path)
        assert load_cache(path) == cache


def test_cache_roundtrip_gzipped():
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "cache.json.gz"
        cache = {cache_key("foo", "en", "es", "google"): "comida"}
        save_cache(cache, path)
        assert load_cache(path) == cache


def test_load_cache_returns_empty_for_missing_file():
    with tempfile.TemporaryDirectory() as d:
        assert load_cache(Path(d) / "does-not-exist.json") == {}
        assert load_cache(Path(d) / "does-not-exist.json.gz") == {}


# --------------------------------------------------------------------------- #
# Analysis on synthetic data                                                  #
# --------------------------------------------------------------------------- #

@pytest.fixture
def small_df():
    """A tiny long-format dataframe with two families × two domains."""
    return pd.DataFrame([
        {"family": "a", "language": "a1", "domain": "x", "bleu": 80, "cosine": 0.99, "ter": 10},
        {"family": "a", "language": "a1", "domain": "y", "bleu": 78, "cosine": 0.98, "ter": 12},
        {"family": "b", "language": "b1", "domain": "x", "bleu": 60, "cosine": 0.97, "ter": 25},
        {"family": "b", "language": "b1", "domain": "y", "bleu": 55, "cosine": 0.96, "ter": 30},
    ])


def test_summary_by_family(small_df):
    out = summary_by(small_df, "family", "bleu")
    assert "mean" in out.columns
    # Family "a" should rank above "b" on BLEU
    assert out.iloc[0].name == "a"


def test_summary_by_ter_sorts_ascending(small_df):
    out = summary_by(small_df, "family", "ter")
    assert out.iloc[0].name == "a"  # smaller TER is better, ranked first


def test_variance_decomposition_sums_to_total(small_df):
    out = variance_decomposition(small_df, "bleu")
    total_row = out[out["factor"] == "total"]
    assert total_row["eta_squared"].iloc[0] == 1.0


def test_anova_returns_required_keys(small_df):
    out = one_way_anova(small_df, "family", "bleu")
    assert set(out.keys()) == {"F", "p", "df_between", "df_within", "eta_squared"}


def test_extreme_cells_picks_correct_extremes(small_df):
    cells = extreme_cells(small_df, "bleu", n=2)
    assert cells["best"].iloc[0]["bleu"] == 80
    assert cells["worst"].iloc[0]["bleu"] == 55
