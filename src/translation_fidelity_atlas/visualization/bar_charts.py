"""
Bar charts: per-family and per-domain mean scores with ±1 SD error bars.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..config import (
    DOMAIN_COLORS,
    DOMAIN_ORDER,
    FAMILY_ORDER,
    TRANSLATOR_COLORS,
    TRANSLATOR_HATCHES,
    TRANSLATOR_ORDER,
    family_tick_label,
    metric_axis_label,
    translator_display_name,
)
from .style import WIDTH_2COL, legend_below, savefig, style_axes


def plot_family_bars(df: pd.DataFrame, output_dir: str | Path) -> None:
    """
    For each translator × metric, plot per-family means grouped by domain.

    Bars are coloured by domain; x-axis is family. Error bars are ±1 SD.
    """
    metrics = [m for m in ("cosine", "bleu", "ter") if m in df.columns]
    output_dir = Path(output_dir)

    for translator in [t for t in TRANSLATOR_ORDER if t in df["translator"].unique()]:
        sub = df[df["translator"] == translator]

        for metric in metrics:
            fig, ax = plt.subplots(figsize=(WIDTH_2COL, 2.9))
            families  = [f for f in FAMILY_ORDER if f in sub["family"].unique()]
            x         = np.arange(len(families))
            n_domains = len(DOMAIN_ORDER)
            bar_w     = 0.8 / n_domains

            for i, domain in enumerate(DOMAIN_ORDER):
                d      = sub[sub["domain"] == domain]
                means  = [d[d["family"] == f][metric].mean() for f in families]
                stds   = [d[d["family"] == f][metric].std()  for f in families]
                offset = (i - n_domains / 2 + 0.5) * bar_w
                ax.bar(
                    x + offset, means, bar_w,
                    yerr=stds, capsize=1.5,
                    color=DOMAIN_COLORS.get(domain, "#999999"),
                    label=domain.capitalize(),
                    linewidth=0.3, edgecolor="white",
                    error_kw={"elinewidth": 0.6, "ecolor": "#5A5A5A"},
                )

            ax.set_xticks(x)
            ax.set_xticklabels([family_tick_label(f) for f in families])
            ax.set_xlabel("Language family")
            ax.set_ylabel(metric_axis_label(metric))
            ax.set_title(
                f"{translator_display_name(translator)} — "
                f"{metric_axis_label(metric).split(' (')[0]} by family and domain"
            )
            ax.set_xlim(-0.5, len(families) - 0.5)
            if metric == "cosine":
                ax.set_ylim(0.0, 1.0)
            style_axes(ax)

            handles, labels = ax.get_legend_handles_labels()
            legend_below(fig, handles, labels, ncol=6, title=None, y=-0.02)
            fig.tight_layout()
            savefig(fig, output_dir / f"bar_family_{metric}_{translator}.png")


def plot_domain_bars(df: pd.DataFrame, output_dir: str | Path) -> None:
    """
    For each metric, plot per-domain means grouped by translator.

    This is the one bar chart that puts the two systems side by side, so the
    translators are separated by hatch as well as colour and stay readable in
    greyscale.
    """
    metrics = [m for m in ("cosine", "bleu", "ter") if m in df.columns]
    output_dir = Path(output_dir)

    for metric in metrics:
        fig, ax = plt.subplots(figsize=(WIDTH_2COL * 0.72, 2.8))
        domains = [d for d in DOMAIN_ORDER if d in df["domain"].unique()]
        translators = [t for t in TRANSLATOR_ORDER if t in df["translator"].unique()]

        x     = np.arange(len(domains))
        bar_w = 0.72 / max(len(translators), 1)

        for i, translator in enumerate(translators):
            sub    = df[df["translator"] == translator]
            means  = [sub[sub["domain"] == d][metric].mean() for d in domains]
            stds   = [sub[sub["domain"] == d][metric].std()  for d in domains]
            offset = (i - (len(translators) - 1) / 2) * bar_w
            ax.bar(
                x + offset, means, bar_w,
                yerr=stds, capsize=1.5,
                color=TRANSLATOR_COLORS.get(translator, "#888888"),
                hatch=TRANSLATOR_HATCHES.get(translator, ""),
                label=translator_display_name(translator),
                linewidth=0.4, edgecolor="white",
                error_kw={"elinewidth": 0.6, "ecolor": "#5A5A5A"},
            )

        ax.set_xticks(x)
        ax.set_xticklabels([d.capitalize() for d in domains])
        ax.set_xlabel("Domain")
        ax.set_ylabel(metric_axis_label(metric))
        ax.set_title(f"{metric_axis_label(metric).split(' (')[0]} by domain")
        ax.set_xlim(-0.5, len(domains) - 0.5)
        style_axes(ax)
        ax.legend(loc="best")
        fig.tight_layout()
        savefig(fig, output_dir / f"bar_domain_{metric}.png")
