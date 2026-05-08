"""
Cross-metric scatter plots, radar profiles, correlation matrices, and
per-family box plots — the figures that summarize the dataset as a whole.
"""

from __future__ import annotations

from math import pi
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import pearsonr

from ..config import (
    FAMILY_ORDER,
    METRIC_LABELS,
    TRANSLATOR_ORDER,
    family_display_name,
)
from ._utils import savefig


# --------------------------------------------------------------------------- #
# Scatter plots — pairwise metric correlations                                #
# --------------------------------------------------------------------------- #

def plot_metric_scatter(df: pd.DataFrame, output_dir: str | Path) -> None:
    """Three scatter plots: cosine vs BLEU, cosine vs TER, BLEU vs TER."""
    output_dir = Path(output_dir)
    pairs = [
        ("cosine", "bleu", "Cosine Similarity", "BLEU"),
        ("cosine", "ter",  "Cosine Similarity", "TER"),
        ("bleu",   "ter",  "BLEU",              "TER"),
    ]
    palette = sns.color_palette("tab10", n_colors=len(FAMILY_ORDER))
    family_color = {f: palette[i] for i, f in enumerate(FAMILY_ORDER)}

    for mx, my, lx, ly in pairs:
        fig, ax = plt.subplots(figsize=(7, 6))
        for family in FAMILY_ORDER:
            sub = df[df["family"] == family].dropna(subset=[mx, my])
            if sub.empty:
                continue
            ax.scatter(
                sub[mx], sub[my],
                color=family_color[family], s=22, alpha=0.6,
                label=family_display_name(family), edgecolors="none",
            )

        valid = df.dropna(subset=[mx, my])
        if len(valid) >= 2:
            r, p = pearsonr(valid[mx], valid[my])
            m, b = np.polyfit(valid[mx], valid[my], 1)
            xs = np.linspace(valid[mx].min(), valid[mx].max(), 200)
            ax.plot(xs, m * xs + b, color="#333", linewidth=1.5,
                    linestyle="--", label=f"OLS  r={r:.3f}")
            p_str = "p < 0.001" if p < 0.001 else f"p = {p:.3f}"
            ax.text(
                0.97, 0.04, f"Pearson r = {r:.3f}\n{p_str}",
                transform=ax.transAxes, ha="right", va="bottom", fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#ccc",
                          alpha=0.85),
            )

        ax.set_xlabel(lx, fontsize=11)
        ax.set_ylabel(ly, fontsize=11)
        ax.set_title(f"Metric Correlation: {lx} vs. {ly}", fontweight="bold")
        ax.legend(title="Family", fontsize=8, title_fontsize=9,
                  loc="upper left", ncol=2)
        fig.tight_layout()
        savefig(fig, output_dir / f"scatter_{mx}_vs_{my}.png")


# --------------------------------------------------------------------------- #
# Radar charts — per-family metric profiles                                   #
# --------------------------------------------------------------------------- #

def plot_radar(df: pd.DataFrame, output_dir: str | Path) -> None:
    """One radar per translator; axes are cosine, BLEU(/100), and 1−TER/100."""
    output_dir = Path(output_dir)
    axes_labels = ["Cosine\nSimilarity", "BLEU\n(norm.)", "TER-inv\n(1-TER/100)"]
    N = len(axes_labels)
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]

    palette = sns.color_palette("tab10", n_colors=len(FAMILY_ORDER))

    for translator in [t for t in TRANSLATOR_ORDER if t in df["translator"].unique()]:
        sub = df[df["translator"] == translator]
        fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
        ax.set_theta_offset(pi / 2)
        ax.set_theta_direction(-1)
        ax.set_thetagrids(np.degrees(angles[:-1]), axes_labels, fontsize=10)
        for r in [0.25, 0.5, 0.75, 1.0]:
            ax.plot(angles, [r] * (N + 1), "--", color="#bbb",
                    linewidth=0.6, zorder=0)

        for i, family in enumerate(FAMILY_ORDER):
            fsub = sub[sub["family"] == family].dropna(subset=["cosine", "bleu", "ter"])
            if fsub.empty:
                continue
            vals = [
                fsub["cosine"].mean(),
                fsub["bleu"].mean() / 100,
                1.0 - (fsub["ter"].mean() / 100),
            ]
            vals += vals[:1]
            ax.plot(angles, vals, linewidth=1.8, color=palette[i],
                    label=family_display_name(family))
            ax.fill(angles, vals, alpha=0.08, color=palette[i])

        ax.set_ylim(0, 1)
        ax.set_title(f"{translator.capitalize()} — Family Metric Profiles",
                     fontweight="bold", pad=20)
        ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.15),
                  fontsize=8.5, title="Family", title_fontsize=9)
        fig.tight_layout()
        savefig(fig, output_dir / f"radar_{translator}.png")


# --------------------------------------------------------------------------- #
# Correlation matrices                                                        #
# --------------------------------------------------------------------------- #

def plot_correlation_matrix(df: pd.DataFrame, output_dir: str | Path) -> None:
    """3×3 Pearson r heatmap of (cosine, bleu, ter) per translator."""
    output_dir = Path(output_dir)

    def _sig(p: float) -> str:
        if p < 0.001: return "***"
        if p < 0.01:  return "**"
        if p < 0.05:  return "*"
        return ""

    for translator in [t for t in TRANSLATOR_ORDER if t in df["translator"].unique()]:
        sub = df[df["translator"] == translator][["cosine", "bleu", "ter"]].dropna()
        metrics = ["cosine", "bleu", "ter"]
        n = len(metrics)
        r_mat = np.ones((n, n))
        ann_mat = np.empty((n, n), dtype=object)

        for i, m1 in enumerate(metrics):
            for j, m2 in enumerate(metrics):
                if i == j:
                    ann_mat[i][j] = "—"
                    continue
                r, p = pearsonr(sub[m1], sub[m2])
                r_mat[i][j] = r
                ann_mat[i][j] = f"{r:.3f}{_sig(p)}"

        fig, ax = plt.subplots(figsize=(5, 4))
        sns.heatmap(
            r_mat, ax=ax, cmap="coolwarm", vmin=-1, vmax=1,
            annot=ann_mat, fmt="", linewidths=0.5, square=True,
            xticklabels=[m.upper() for m in metrics],
            yticklabels=[m.upper() for m in metrics],
            cbar_kws={"label": "Pearson r"},
        )
        ax.set_title(
            f"{translator.capitalize()} — Metric Intercorrelations\n"
            "(*p<.05  **p<.01  ***p<.001)",
            fontweight="bold",
        )
        fig.tight_layout()
        savefig(fig, output_dir / f"corr_matrix_{translator}.png")


# --------------------------------------------------------------------------- #
# Box plots — per-family variance                                             #
# --------------------------------------------------------------------------- #

def plot_family_boxplots(df: pd.DataFrame, output_dir: str | Path) -> None:
    """Per-translator, per-metric box plot of distributions across families."""
    output_dir = Path(output_dir)
    metrics = [m for m in ("cosine", "bleu", "ter") if m in df.columns]

    for translator in [t for t in TRANSLATOR_ORDER if t in df["translator"].unique()]:
        sub = df[df["translator"] == translator]
        for metric in metrics:
            families = [f for f in FAMILY_ORDER if f in sub["family"].unique()]
            data = [sub[sub["family"] == f][metric].dropna().values for f in families]

            fig, ax = plt.subplots(figsize=(10, 4.5))
            bplot = ax.boxplot(
                data, patch_artist=True, notch=True,
                medianprops=dict(color="black", linewidth=2),
                flierprops=dict(marker=".", markersize=3, alpha=0.4),
            )
            palette = sns.color_palette("Set2", n_colors=len(families))
            for patch, color in zip(bplot["boxes"], palette):
                patch.set_facecolor(color)
                patch.set_alpha(0.75)

            ax.set_xticks(range(1, len(families) + 1))
            ax.set_xticklabels(
                [family_display_name(f).replace(" ", "\n") for f in families],
                fontsize=9,
            )
            ax.set_xlabel("Language Family")
            ax.set_ylabel(METRIC_LABELS[metric])
            ax.set_title(
                f"{translator.capitalize()} — {METRIC_LABELS[metric]} by Family",
                fontweight="bold",
            )
            fig.tight_layout()
            savefig(fig, output_dir / f"boxplot_{metric}_{translator}.png")
