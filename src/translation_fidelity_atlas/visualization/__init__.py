"""
All figure-generating functions, plus a single master entrypoint
:func:`run_all` that loads result CSVs and emits every figure.
"""

from __future__ import annotations

import logging
import os
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
from .heatmaps import plot_family_heatmaps

log = logging.getLogger(__name__)


def run_all(
    long_csv:      str | os.PathLike = "data/results/google/back_translation_long.csv",
    chain_csv:     str | os.PathLike = "data/results/google/telephone_chain.csv",
    roundtrip_csv: str | os.PathLike = "data/results/google/round_trip.csv",
    output_dir:    str | os.PathLike = "figures",
) -> None:
    """
    Generate every figure the project produces.

    Missing chain / round-trip CSVs are skipped with a warning rather than
    raised — useful while developing those experiments.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    log.info("Loading main results: %s", long_csv)
    df = pd.read_csv(long_csv)
    log.info("  %d rows", len(df))

    log.info("[1/8] Per-family heatmaps ...")
    plot_family_heatmaps(df, output_dir)

    log.info("[2/8] Per-family bar charts ...")
    plot_family_bars(df, output_dir)

    log.info("[3/8] Per-domain bar charts ...")
    plot_domain_bars(df, output_dir)

    log.info("[4/8] Metric-pair scatter plots ...")
    plot_metric_scatter(df, output_dir)

    log.info("[5/8] Radar charts ...")
    plot_radar(df, output_dir)

    log.info("[6/8] Family box plots ...")
    plot_family_boxplots(df, output_dir)

    log.info("[7/8] Metric correlation matrices ...")
    plot_correlation_matrix(df, output_dir)

    if Path(chain_csv).exists():
        log.info("[8a] Telephone-chain degradation curves ...")
        chain_df = pd.read_csv(chain_csv)
        plot_chain_degradation(chain_df, output_dir)
    else:
        log.warning("Skipping chain plots — %s not found", chain_csv)

    if Path(roundtrip_csv).exists():
        log.info("[8b] Round-trip asymmetry plots ...")
        rt_df = pd.read_csv(roundtrip_csv)
        plot_round_trip(rt_df, output_dir)
        plot_asymmetry_heatmap(rt_df, output_dir)
    else:
        log.warning("Skipping round-trip plots — %s not found", roundtrip_csv)

    log.info("All figures written to: %s", output_dir)


__all__ = [
    "run_all",
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
