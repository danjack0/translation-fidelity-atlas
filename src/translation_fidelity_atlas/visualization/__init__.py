"""
All figure-generating functions, plus a single master entrypoint
:func:`run_all` that loads result CSVs and emits every figure.

Styling lives in :mod:`.style` and nowhere else; importing any plotting module
applies it.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from .aggregate_plots import (
    plot_correlation_matrix,
    plot_family_boxplots,
    plot_metric_scatter,
    plot_radar,
)
from .bar_charts import plot_domain_bars, plot_family_bars
from .chain_plots import (
    plot_asymmetry_heatmap,
    plot_chain_degradation,
    plot_round_trip,
)
from .heatmaps import plot_all_language_heatmap, plot_family_heatmaps
from .style import apply_style, savefig

log = logging.getLogger(__name__)

PathLike = str | os.PathLike

#: Both systems ran all three protocols, so every default here covers both.
#: ``combined_long.csv`` is the concatenation of the two per-backend long CSVs;
#: the per-translator figures split it back out internally.
DEFAULT_LONG_CSV: str = "data/results/combined_long.csv"
DEFAULT_CHAIN_CSVS: tuple[str, ...] = (
    "data/results/google/telephone_chain.csv",
    "data/results/nllb/telephone_chain.csv",
)
DEFAULT_ROUNDTRIP_CSVS: tuple[str, ...] = (
    "data/results/google/round_trip.csv",
    "data/results/nllb/round_trip.csv",
)


def _load_many(paths: PathLike | Sequence[PathLike] | None,
               what: str) -> pd.DataFrame | None:
    """Read and concatenate however many CSVs were given; warn on missing ones."""
    if paths is None:
        return None
    if isinstance(paths, (str, os.PathLike)):
        paths = [paths]

    frames: list[pd.DataFrame] = []
    for p in paths:
        if Path(p).exists():
            log.info("  %s: %s", what, p)
            frames.append(pd.read_csv(p))
        else:
            log.warning("  Skipping %s — %s not found", what, p)

    if not frames:
        return None
    df = pd.concat(frames, ignore_index=True)
    log.info("  %s: %d rows, translators=%s",
             what, len(df), sorted(df["translator"].unique()))
    return df


def run_all(
    long_csv:      PathLike = DEFAULT_LONG_CSV,
    chain_csv:     PathLike | Sequence[PathLike] | None = DEFAULT_CHAIN_CSVS,
    roundtrip_csv: PathLike | Sequence[PathLike] | None = DEFAULT_ROUNDTRIP_CSVS,
    output_dir:    PathLike = "figures",
) -> None:
    """
    Generate every figure the project produces, for every backend present.

    ``chain_csv`` and ``roundtrip_csv`` each accept a single path or a sequence
    of paths, which are concatenated — that is how both translation systems end
    up in the chain and round-trip figures. Missing CSVs are skipped with a
    warning rather than raised.

    Step [1/9] is the full-coverage overview — every language at once, both
    systems side by side, rows banded by family — and step [2/9] the per-family
    detail behind it. Both come from ``long_csv``; neither calls a translator.
    """
    apply_style()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    log.info("Loading main results: %s", long_csv)
    df = pd.read_csv(long_csv)
    log.info("  %d rows, translators=%s", len(df), sorted(df["translator"].unique()))

    log.info("[1/9] Full-coverage heatmaps (all languages, both systems) ...")
    plot_all_language_heatmap(df, output_dir)

    log.info("[2/9] Per-family heatmaps ...")
    plot_family_heatmaps(df, output_dir)

    log.info("[3/9] Per-family bar charts ...")
    plot_family_bars(df, output_dir)

    log.info("[4/9] Per-domain bar charts ...")
    plot_domain_bars(df, output_dir)

    log.info("[5/9] Metric-pair scatter plots ...")
    plot_metric_scatter(df, output_dir)

    log.info("[6/9] Radar charts ...")
    plot_radar(df, output_dir)

    log.info("[7/9] Family box plots ...")
    plot_family_boxplots(df, output_dir)

    log.info("[8/9] Metric correlation matrices ...")
    plot_correlation_matrix(df, output_dir)

    log.info("[9a] Telephone-chain degradation curves ...")
    chain_df = _load_many(chain_csv, "chain")
    if chain_df is not None:
        plot_chain_degradation(chain_df, output_dir)

    log.info("[9b] Round-trip asymmetry plots ...")
    rt_df = _load_many(roundtrip_csv, "round-trip")
    if rt_df is not None:
        plot_round_trip(rt_df, output_dir)
        plot_asymmetry_heatmap(rt_df, output_dir)

    log.info("All figures written to: %s", output_dir)


__all__ = [
    "run_all",
    "savefig",
    "apply_style",
    "DEFAULT_LONG_CSV",
    "DEFAULT_CHAIN_CSVS",
    "DEFAULT_ROUNDTRIP_CSVS",
    "plot_all_language_heatmap",
    "plot_family_heatmaps",
    "plot_family_bars",
    "plot_domain_bars",
    "plot_metric_scatter",
    "plot_radar",
    "plot_family_boxplots",
    "plot_correlation_matrix",
    "plot_chain_degradation",
    "plot_round_trip",
    "plot_asymmetry_heatmap",
]
