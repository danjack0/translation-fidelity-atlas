"""
Visualizations for the telephone-chain and round-trip experiments.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from ..config import (
    CHAIN_ORDER_STYLES,
    DOMAIN_ORDER,
    METRIC_HIGHER_IS_BETTER,
    METRIC_LABELS,
    TRANSLATOR_COLORS,
    TRANSLATOR_ORDER,
)
from ._utils import savefig


# --------------------------------------------------------------------------- #
# Chain degradation curves                                                    #
# --------------------------------------------------------------------------- #

def plot_chain_degradation(chain_df: pd.DataFrame, output_dir: str | Path) -> None:
    """
    Per-metric grid: rows = translators, cols = domains. Lines show fidelity
    versus hop number for each chain order.
    """
    output_dir = Path(output_dir)
    domains = [d for d in DOMAIN_ORDER if d in chain_df["domain"].unique()]
    translators = [t for t in TRANSLATOR_ORDER if t in chain_df["translator"].unique()]
    metrics = [m for m in ("cosine", "bleu", "ter") if m in chain_df.columns]

    for metric in metrics:
        n_rows = len(translators)
        n_cols = len(domains)
        if n_rows == 0 or n_cols == 0:
            continue

        fig, axes = plt.subplots(
            n_rows, n_cols,
            figsize=(3.2 * n_cols, 3.0 * n_rows),
            sharex=True, sharey=True, squeeze=False,
        )

        for ri, translator in enumerate(translators):
            for ci, domain in enumerate(domains):
                ax = axes[ri][ci]
                sub = chain_df[
                    (chain_df["translator"] == translator) &
                    (chain_df["domain"] == domain)
                ].dropna(subset=[metric])

                for order, style in CHAIN_ORDER_STYLES.items():
                    grp = sub[sub["order"] == order].sort_values("hop")
                    if grp.empty:
                        continue
                    ax.plot(
                        grp["hop"], grp[metric],
                        color=TRANSLATOR_COLORS.get(translator, "#888"),
                        label=order, **style,
                        linewidth=1.6, markersize=5,
                    )

                if ci == 0:
                    ax.set_ylabel(f"{translator.capitalize()}\n{METRIC_LABELS[metric]}",
                                  fontsize=8)
                if ri == 0:
                    ax.set_title(domain.capitalize(), fontsize=9, fontweight="bold")

                arrow = "↑" if METRIC_HIGHER_IS_BETTER[metric] else "↓"
                ax.text(
                    0.97,
                    0.96 if METRIC_HIGHER_IS_BETTER[metric] else 0.04,
                    arrow, transform=ax.transAxes, ha="right",
                    va="top" if METRIC_HIGHER_IS_BETTER[metric] else "bottom",
                    fontsize=10, color="#555",
                )

        handles = [
            plt.Line2D([0], [0], **CHAIN_ORDER_STYLES[o], color="#555",
                       linewidth=1.6, markersize=5, label=o.capitalize())
            for o in CHAIN_ORDER_STYLES
        ]
        fig.legend(handles=handles, title="Chain Order",
                   loc="lower center", ncol=3, fontsize=9, title_fontsize=9,
                   bbox_to_anchor=(0.5, -0.02))
        fig.suptitle(f"Telephone-Chain Degradation — {METRIC_LABELS[metric]}",
                     fontweight="bold", y=1.01)
        fig.tight_layout()
        savefig(fig, output_dir / f"chain_degradation_{metric}.png")


# --------------------------------------------------------------------------- #
# ABA vs. BAB round-trip                                                      #
# --------------------------------------------------------------------------- #

def plot_round_trip(rt_df: pd.DataFrame, output_dir: str | Path) -> None:
    """Side-by-side bars per language for ABA vs BAB on each metric."""
    output_dir = Path(output_dir)
    metrics = {"cosine": "Cosine Similarity", "bleu": "BLEU",
               "ter": "TER (lower = better)"}
    dir_colors = {"ABA": "#1E88E5", "BAB": "#FB8C00"}

    for translator in [t for t in TRANSLATOR_ORDER if t in rt_df["translator"].unique()]:
        sub = rt_df[rt_df["translator"] == translator]
        langs = sorted(sub["language"].unique())
        if not langs:
            continue

        fig, axes = plt.subplots(
            1, 3, figsize=(15, max(5, len(langs) * 0.38 + 2)), sharey=True,
        )

        for ax, (metric, label) in zip(axes, metrics.items()):
            grp = (sub.groupby(["language", "direction"])[metric]
                       .mean().reset_index())
            y = np.arange(len(langs))
            bar_h = 0.35

            for i, direction in enumerate(["ABA", "BAB"]):
                d = grp[grp["direction"] == direction]
                vals = [
                    d[d["language"] == lang][metric].values[0]
                    if lang in d["language"].values else 0.0
                    for lang in langs
                ]
                offset = (i - 0.5) * bar_h
                ax.barh(y + offset, vals, bar_h,
                        color=dir_colors[direction], label=direction, alpha=0.85)

            ax.set_yticks(y)
            ax.set_yticklabels(langs, fontsize=8)
            ax.set_xlabel(label, fontsize=9)
            ax.set_title(label, fontweight="bold", fontsize=9)
            ax.invert_yaxis()

        handles = [plt.Rectangle((0, 0), 1, 1, color=dir_colors[d], alpha=0.85, label=d)
                   for d in ["ABA", "BAB"]]
        fig.legend(handles=handles, title="Direction",
                   loc="lower center", ncol=2, fontsize=10, title_fontsize=10,
                   bbox_to_anchor=(0.5, -0.04))
        fig.suptitle(
            f"{translator.capitalize()} — Round-Trip Asymmetry (ABA vs BAB)",
            fontweight="bold",
        )
        fig.tight_layout()
        savefig(fig, output_dir / f"roundtrip_{translator}.png")


def plot_asymmetry_heatmap(rt_df: pd.DataFrame, output_dir: str | Path) -> None:
    """|ABA cosine − BAB cosine| heatmap across translators × languages."""
    output_dir = Path(output_dir)
    rows: list[dict] = []

    for translator in TRANSLATOR_ORDER:
        sub = rt_df[rt_df["translator"] == translator]
        if sub.empty:
            continue
        grp = sub.groupby(["language", "direction"])["cosine"].mean().reset_index()
        for lang in sub["language"].unique():
            aba = grp[(grp["language"] == lang) & (grp["direction"] == "ABA")]["cosine"]
            bab = grp[(grp["language"] == lang) & (grp["direction"] == "BAB")]["cosine"]
            if aba.empty or bab.empty:
                continue
            rows.append({
                "translator": translator.capitalize(),
                "language":   lang,
                "asymmetry":  round(abs(aba.values[0] - bab.values[0]), 4),
            })

    if not rows:
        return

    pivot = (
        pd.DataFrame(rows)
        .pivot(index="language", columns="translator", values="asymmetry")
        .sort_values(by=pd.DataFrame(rows)["translator"].iloc[0], ascending=False)
    )

    fig, ax = plt.subplots(figsize=(6, max(6, len(pivot) * 0.35 + 2)))
    sns.heatmap(pivot, ax=ax, cmap="YlOrRd", annot=True, fmt=".3f",
                linewidths=0.4, linecolor="#eee",
                cbar_kws={"label": "|ABA cosine − BAB cosine|"})
    ax.set_title("Directional Asymmetry  |ABA − BAB|  (Cosine)", fontweight="bold")
    ax.set_xlabel("Translator")
    ax.set_ylabel("Language")
    fig.tight_layout()
    savefig(fig, output_dir / "asymmetry_heatmap.png")
