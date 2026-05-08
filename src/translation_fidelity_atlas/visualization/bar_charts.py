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
    METRIC_HIGHER_IS_BETTER,
    METRIC_LABELS,
    TRANSLATOR_COLORS,
    TRANSLATOR_ORDER,
    family_display_name,
)
from ._utils import savefig


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
            fig, ax = plt.subplots(figsize=(11, 5))
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
                    yerr=stds, capsize=3,
                    color=DOMAIN_COLORS.get(domain, "#999"),
                    label=domain.capitalize(), alpha=0.88,
                    error_kw={"elinewidth": 0.8, "alpha": 0.6},
                )

            ax.set_xticks(x)
            ax.set_xticklabels(
                [family_display_name(f).replace(" ", "\n") for f in families],
                fontsize=9,
            )
            ax.set_xlabel("Language Family")
            ax.set_ylabel(METRIC_LABELS[metric])
            direction = "↑ higher is better" if METRIC_HIGHER_IS_BETTER[metric] else "↓ lower is better"
            ax.set_title(
                f"{translator.capitalize()} — {METRIC_LABELS[metric]} by Family & Domain  ({direction})",
                fontweight="bold",
            )
            if metric == "cosine":
                ax.set_ylim(0.0, 1.0)
            ax.legend(title="Domain", loc="lower left", ncol=2,
                      fontsize=8, title_fontsize=8)
            fig.tight_layout()
            savefig(fig, output_dir / f"bar_family_{metric}_{translator}.png")


def plot_domain_bars(df: pd.DataFrame, output_dir: str | Path) -> None:
    """For each metric, plot per-domain means grouped by translator."""
    metrics = [m for m in ("cosine", "bleu", "ter") if m in df.columns]
    output_dir = Path(output_dir)

    for metric in metrics:
        fig, ax = plt.subplots(figsize=(9, 4.5))
        domains = [d for d in DOMAIN_ORDER if d in df["domain"].unique()]
        translators = [t for t in TRANSLATOR_ORDER if t in df["translator"].unique()]

        x       = np.arange(len(domains))
        bar_w   = 0.8 / max(len(translators), 1)

        for i, translator in enumerate(translators):
            sub    = df[df["translator"] == translator]
            means  = [sub[sub["domain"] == d][metric].mean() for d in domains]
            stds   = [sub[sub["domain"] == d][metric].std()  for d in domains]
            offset = (i - (len(translators) - 1) / 2) * bar_w
            ax.bar(
                x + offset, means, bar_w,
                yerr=stds, capsize=3,
                color=TRANSLATOR_COLORS.get(translator, "#888"),
                label=translator.capitalize(), alpha=0.88,
                error_kw={"elinewidth": 0.8, "alpha": 0.6},
            )

        ax.set_xticks(x)
        ax.set_xticklabels([d.capitalize() for d in domains], fontsize=10)
        ax.set_xlabel("Domain")
        ax.set_ylabel(METRIC_LABELS[metric])
        direction = "↑ higher is better" if METRIC_HIGHER_IS_BETTER[metric] else "↓ lower is better"
        ax.set_title(f"{METRIC_LABELS[metric]} by Domain ({direction})",
                     fontweight="bold")
        ax.legend(title="Translator", fontsize=9, title_fontsize=9)
        fig.tight_layout()
        savefig(fig, output_dir / f"bar_domain_{metric}.png")
