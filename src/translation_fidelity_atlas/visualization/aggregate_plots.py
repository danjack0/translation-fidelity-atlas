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
    FAMILY_COLORS,
    FAMILY_ORDER,
    METRIC_LABELS,
    METRIC_SHORT_LABELS,
    TRANSLATOR_MARKERS,
    TRANSLATOR_ORDER,
    family_display_name,
    family_tick_label,
    metric_axis_label,
    translator_display_name,
)
from .style import (
    CMAP_DIVERGING,
    WIDTH_1COL,
    WIDTH_2COL,
    legend_below,
    savefig,
    style_axes,
    style_heatmap_axes,
)


# --------------------------------------------------------------------------- #
# Scatter plots — pairwise metric correlations                                #
# --------------------------------------------------------------------------- #

def plot_metric_scatter(df: pd.DataFrame, output_dir: str | Path) -> None:
    """
    Three scatter plots: cosine vs BLEU, cosine vs TER, BLEU vs TER.

    Split into one panel per translation system. Pooling both systems into a
    single cloud produces a correlation that belongs to neither of them — the
    pooled r for cosine vs BLEU is 0.814, while the two systems are at 0.651
    and 0.761 — so each panel carries its own n, r and fit, and the pooled
    figure is reported in the caption line rather than drawn as if it were one
    population.
    """
    output_dir = Path(output_dir)
    pairs = [
        ("cosine", "bleu", "Cosine similarity", "BLEU"),
        ("cosine", "ter",  "Cosine similarity", "TER"),
        ("bleu",   "ter",  "BLEU",              "TER"),
    ]
    translators = [t for t in TRANSLATOR_ORDER if t in df["translator"].unique()]
    if not translators:
        return

    for mx, my, lx, ly in pairs:
        n_panels = len(translators)
        fig, axes = plt.subplots(
            1, n_panels,
            figsize=(WIDTH_2COL if n_panels > 1 else WIDTH_1COL * 1.35, 3.1),
            squeeze=False, sharex=True, sharey=True,
        )

        for ax, translator in zip(axes[0], translators):
            tsub = df[df["translator"] == translator]
            marker = TRANSLATOR_MARKERS.get(translator, "o")

            for family in FAMILY_ORDER:
                fsub = tsub[tsub["family"] == family].dropna(subset=[mx, my])
                if fsub.empty:
                    continue
                ax.scatter(
                    fsub[mx], fsub[my],
                    color=FAMILY_COLORS[family], s=14, alpha=0.85,
                    marker=marker, linewidths=0.3, edgecolors="#33333366",
                    label=family_display_name(family),
                )

            valid = tsub.dropna(subset=[mx, my])
            if len(valid) >= 2:
                r, p = pearsonr(valid[mx], valid[my])
                m, b = np.polyfit(valid[mx], valid[my], 1)
                xs = np.linspace(valid[mx].min(), valid[mx].max(), 200)
                ax.plot(xs, m * xs + b, color="#2B2B2B", linewidth=1.1,
                        linestyle="--", zorder=5)
                p_str = "p < 0.001" if p < 0.001 else f"p = {p:.3f}"
                ax.set_title(
                    f"{translator_display_name(translator)}\n"
                    f"r = {r:.3f}, {p_str}, n = {len(valid)}"
                )

            ax.set_xlabel(lx)
            style_axes(ax, grid_axis="both")

        axes[0][0].set_ylabel(ly)

        handles = [
            plt.Line2D([0], [0], linestyle="none", marker="o", markersize=4,
                       color=FAMILY_COLORS[f], label=family_display_name(f))
            for f in FAMILY_ORDER if f in df["family"].unique()
        ]
        handles.append(plt.Line2D([0], [0], linestyle="--", color="#2B2B2B",
                                  linewidth=1.1, label="OLS fit"))
        legend_below(fig, handles, [h.get_label() for h in handles],
                     ncol=5, title=None, y=-0.02)

        pooled = df.dropna(subset=[mx, my])
        if len(translators) > 1 and len(pooled) >= 2:
            r_pool, _ = pearsonr(pooled[mx], pooled[my])
            fig.text(
                0.5, -0.19,
                f"Panels are separate populations. Pooled across both systems: "
                f"r = {r_pool:.3f} (n = {len(pooled)}).",
                ha="center", va="top", fontsize=6.5, color="#5A5A5A",
            )

        fig.suptitle(f"{lx} vs. {ly}")
        fig.tight_layout()
        savefig(fig, output_dir / f"scatter_{mx}_vs_{my}.png")


# --------------------------------------------------------------------------- #
# Radar charts — per-family metric profiles                                   #
# --------------------------------------------------------------------------- #

def plot_radar(df: pd.DataFrame, output_dir: str | Path) -> None:
    """One radar per translator; axes are cosine, BLEU(/100), and 1−TER/100."""
    output_dir = Path(output_dir)
    axes_labels = ["Cosine\nsimilarity", "BLEU\n(normalised)", "1 − TER/100"]
    N = len(axes_labels)
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]

    for translator in [t for t in TRANSLATOR_ORDER if t in df["translator"].unique()]:
        sub = df[df["translator"] == translator]
        fig, ax = plt.subplots(figsize=(WIDTH_1COL * 1.25, 4.0),
                               subplot_kw=dict(polar=True))
        ax.set_theta_offset(pi / 2)
        ax.set_theta_direction(-1)
        ax.set_thetagrids(np.degrees(angles[:-1]), axes_labels)
        ax.set_rlabel_position(180 / N)
        ax.grid(True, color="#DBDBDB", linewidth=0.5)
        ax.spines["polar"].set_edgecolor("#BFBFBF")
        ax.spines["polar"].set_linewidth(0.7)

        for family in FAMILY_ORDER:
            fsub = sub[sub["family"] == family].dropna(subset=["cosine", "bleu", "ter"])
            if fsub.empty:
                continue
            vals = [
                fsub["cosine"].mean(),
                fsub["bleu"].mean() / 100,
                1.0 - (fsub["ter"].mean() / 100),
            ]
            vals += vals[:1]
            ax.plot(angles, vals, linewidth=1.3, color=FAMILY_COLORS[family],
                    label=family_display_name(family))
            ax.fill(angles, vals, alpha=0.06, color=FAMILY_COLORS[family])

        ax.set_ylim(0, 1)
        ax.set_yticks([0.25, 0.5, 0.75, 1.0])
        ax.tick_params(labelsize=6.5)
        ax.set_title(f"{translator_display_name(translator)} — family metric profiles",
                     pad=14)

        handles, labels = ax.get_legend_handles_labels()
        legend_below(fig, handles, labels, ncol=4, title=None, y=0.02)
        fig.tight_layout()
        savefig(fig, output_dir / f"radar_{translator}.png")


# --------------------------------------------------------------------------- #
# Correlation matrices                                                        #
# --------------------------------------------------------------------------- #

def plot_correlation_matrix(df: pd.DataFrame, output_dir: str | Path) -> None:
    """3×3 Pearson r heatmap of (cosine, BLEU, TER) per translator."""
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
                    # The diagonal is 1.0 by construction. Leaving it coloured
                    # puts three saturated cells carrying no information in the
                    # middle of the figure, so it is masked out instead.
                    r_mat[i][j] = np.nan
                    ann_mat[i][j] = ""
                    continue
                r, p = pearsonr(sub[m1], sub[m2])
                r_mat[i][j] = r
                ann_mat[i][j] = f"{r:.3f}{_sig(p)}"

        labels = [METRIC_SHORT_LABELS[m] for m in metrics]
        fig, ax = plt.subplots(figsize=(WIDTH_1COL, 2.7))
        sns.heatmap(
            r_mat, ax=ax, cmap=CMAP_DIVERGING, vmin=-1, vmax=1,
            annot=ann_mat, fmt="", annot_kws={"fontsize": 7.0},
            linewidths=0.5, linecolor="white", square=True,
            xticklabels=labels, yticklabels=labels,
            cbar_kws={"label": "Pearson r", "pad": 0.02},
        )
        ax.set_yticklabels(labels, rotation=0)
        ax.set_title(
            f"{translator_display_name(translator)} — metric intercorrelations"
        )
        ax.text(0.5, -0.16, "* p < .05    ** p < .01    *** p < .001",
                transform=ax.transAxes, ha="center", va="top",
                fontsize=6.5, color="#5A5A5A")
        style_heatmap_axes(ax, cbar_label="Pearson r")
        fig.tight_layout()
        savefig(fig, output_dir / f"corr_matrix_{translator}.png")


# --------------------------------------------------------------------------- #
# Box plots — per-family variance                                             #
# --------------------------------------------------------------------------- #

def plot_family_boxplots(df: pd.DataFrame, output_dir: str | Path) -> None:
    """
    Per-translator, per-metric box plot of distributions across families.

    Box fills use the shared family palette, so a family is the same colour
    here as in the scatter and radar figures. No legend: the x-axis already
    names every family.
    """
    output_dir = Path(output_dir)
    metrics = [m for m in ("cosine", "bleu", "ter") if m in df.columns]

    for translator in [t for t in TRANSLATOR_ORDER if t in df["translator"].unique()]:
        sub = df[df["translator"] == translator]
        for metric in metrics:
            families = [f for f in FAMILY_ORDER if f in sub["family"].unique()]
            data = [sub[sub["family"] == f][metric].dropna().values for f in families]

            fig, ax = plt.subplots(figsize=(WIDTH_2COL, 2.7))
            bplot = ax.boxplot(
                data, patch_artist=True, notch=True, widths=0.6,
                medianprops=dict(color="black", linewidth=1.2),
                whiskerprops=dict(color="#3F3F3F", linewidth=0.7),
                capprops=dict(color="#3F3F3F", linewidth=0.7),
                boxprops=dict(linewidth=0.5),
                flierprops=dict(marker=".", markersize=2.5, alpha=0.5,
                                markeredgecolor="#3F3F3F"),
            )
            for patch, family in zip(bplot["boxes"], families):
                patch.set_facecolor(FAMILY_COLORS[family])
                patch.set_alpha(0.80)
                patch.set_edgecolor("#3F3F3F")

            ax.set_xticks(range(1, len(families) + 1))
            ax.set_xticklabels([family_tick_label(f) for f in families])
            ax.set_xlabel("Language family")
            ax.set_ylabel(metric_axis_label(metric))
            ax.set_title(
                f"{translator_display_name(translator)} — "
                f"{METRIC_LABELS[metric]} by family"
            )
            style_axes(ax)
            fig.tight_layout()
            savefig(fig, output_dir / f"boxplot_{metric}_{translator}.png")
