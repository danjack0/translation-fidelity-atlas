"""
Visualizations for the telephone-chain and round-trip experiments.

Every function here emits one figure per translation system *and*, where a
side-by-side comparison is meaningful, one combined figure. Both backends ran
all three protocols, so nothing in this module is Google-only.
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
    METRIC_LABELS,
    TRANSLATOR_COLORS,
    TRANSLATOR_HATCHES,
    TRANSLATOR_ORDER,
    metric_axis_label,
    translator_display_name,
)
from .style import (
    CMAP_INTENSITY,
    WIDTH_1COL,
    WIDTH_2COL,
    legend_below,
    savefig,
    style_axes,
    style_heatmap_axes,
)

#: ABA / BAB are a within-figure comparison, so they carry a hatch as well as
#: a colour and survive greyscale.
_DIR_COLORS = {"ABA": "#0072B2", "BAB": "#E69F00"}
_DIR_HATCHES = {"ABA": "", "BAB": "///"}


# --------------------------------------------------------------------------- #
# Chain degradation curves                                                    #
# --------------------------------------------------------------------------- #

def _chain_panel(ax, sub: pd.DataFrame, metric: str, translator: str) -> None:
    """Draw one (translator × domain) cell of a chain-degradation grid."""
    for order, style in CHAIN_ORDER_STYLES.items():
        grp = sub[sub["order"] == order].sort_values("hop")
        if grp.empty:
            continue
        ax.plot(
            grp["hop"], grp[metric],
            color=TRANSLATOR_COLORS.get(translator, "#888888"),
            label=order, **style,
            linewidth=1.2, markersize=3.0, markeredgewidth=0.0,
        )
    ax.set_xticks(sorted(sub["hop"].unique()))
    style_axes(ax)


def plot_chain_degradation(chain_df: pd.DataFrame, output_dir: str | Path) -> None:
    """
    Fidelity versus hop number, per chain order.

    Emits one figure per translator (``chain_degradation_{metric}_{translator}``)
    plus a combined figure whose rows are the two systems
    (``chain_degradation_{metric}``).
    """
    output_dir = Path(output_dir)
    domains = [d for d in DOMAIN_ORDER if d in chain_df["domain"].unique()]
    translators = [t for t in TRANSLATOR_ORDER if t in chain_df["translator"].unique()]
    metrics = [m for m in ("cosine", "bleu", "ter") if m in chain_df.columns]
    if not translators or not domains:
        return

    order_handles = [
        plt.Line2D([0], [0], **CHAIN_ORDER_STYLES[o], color="#3F3F3F",
                   linewidth=1.2, markersize=3.0, label=o.capitalize())
        for o in CHAIN_ORDER_STYLES
    ]
    order_labels = [h.get_label() for h in order_handles]

    for metric in metrics:
        # ---- one figure per system ---------------------------------------- #
        for translator in translators:
            fig, axes = plt.subplots(
                1, len(domains), figsize=(WIDTH_2COL, 2.1),
                sharex=True, sharey=True, squeeze=False,
            )
            for ci, domain in enumerate(domains):
                ax = axes[0][ci]
                sub = chain_df[
                    (chain_df["translator"] == translator) &
                    (chain_df["domain"] == domain)
                ].dropna(subset=[metric])
                _chain_panel(ax, sub, metric, translator)
                ax.set_title(domain.capitalize(), fontsize=7.5)
                ax.set_xlabel("Hop")
            axes[0][0].set_ylabel(metric_axis_label(metric))

            legend_below(fig, order_handles, order_labels, ncol=3,
                         title="Chain order", y=-0.04)
            fig.suptitle(
                f"{translator_display_name(translator)} — telephone-chain "
                f"degradation, {METRIC_LABELS[metric]}"
            )
            fig.tight_layout()
            savefig(fig, output_dir / f"chain_degradation_{metric}_{translator}.png")

        # ---- combined: one row per system --------------------------------- #
        n_rows = len(translators)
        fig, axes = plt.subplots(
            n_rows, len(domains),
            figsize=(WIDTH_2COL, 1.9 * n_rows + 0.4),
            sharex=True, sharey=True, squeeze=False,
        )
        for ri, translator in enumerate(translators):
            for ci, domain in enumerate(domains):
                ax = axes[ri][ci]
                sub = chain_df[
                    (chain_df["translator"] == translator) &
                    (chain_df["domain"] == domain)
                ].dropna(subset=[metric])
                _chain_panel(ax, sub, metric, translator)
                if ri == 0:
                    ax.set_title(domain.capitalize(), fontsize=7.5)
                if ri == n_rows - 1:
                    ax.set_xlabel("Hop")
            # The row label names the system, so the comparison does not rest
            # on the line colour alone.
            axes[ri][0].set_ylabel(
                f"{translator_display_name(translator)}\n{METRIC_LABELS[metric]}",
                fontsize=7.0,
            )

        legend_below(fig, order_handles, order_labels, ncol=3,
                     title="Chain order", y=-0.01)
        fig.suptitle(f"Telephone-chain degradation — {METRIC_LABELS[metric]}")
        fig.tight_layout()
        savefig(fig, output_dir / f"chain_degradation_{metric}.png")


# --------------------------------------------------------------------------- #
# ABA vs. BAB round-trip                                                      #
# --------------------------------------------------------------------------- #

def plot_round_trip(rt_df: pd.DataFrame, output_dir: str | Path) -> None:
    """Side-by-side bars per language for ABA vs BAB on each metric."""
    output_dir = Path(output_dir)
    metrics = [m for m in ("cosine", "bleu", "ter") if m in rt_df.columns]

    for translator in [t for t in TRANSLATOR_ORDER if t in rt_df["translator"].unique()]:
        sub = rt_df[rt_df["translator"] == translator]
        langs = sorted(sub["language"].unique())
        if not langs:
            continue

        fig, axes = plt.subplots(
            1, len(metrics), figsize=(WIDTH_2COL, max(2.0, len(langs) * 0.26 + 1.1)),
            sharey=True, squeeze=False,
        )

        for ax, metric in zip(axes[0], metrics):
            grp = (sub.groupby(["language", "direction"])[metric]
                       .mean().reset_index())
            y = np.arange(len(langs))
            bar_h = 0.36

            for i, direction in enumerate(["ABA", "BAB"]):
                d = grp[grp["direction"] == direction]
                vals = [
                    d[d["language"] == lang][metric].values[0]
                    if lang in d["language"].values else 0.0
                    for lang in langs
                ]
                offset = (i - 0.5) * bar_h
                ax.barh(y + offset, vals, bar_h,
                        color=_DIR_COLORS[direction],
                        hatch=_DIR_HATCHES[direction],
                        edgecolor="white", linewidth=0.4,
                        label=direction)

            ax.set_yticks(y)
            ax.set_yticklabels(langs)
            # The x-label already names the metric; a panel title would only
            # repeat it.
            ax.set_xlabel(metric_axis_label(metric))
            style_axes(ax, grid_axis="x")

        axes[0][0].invert_yaxis()
        axes[0][0].set_ylabel("Language")

        handles = [
            plt.Rectangle((0, 0), 1, 1, facecolor=_DIR_COLORS[d],
                          hatch=_DIR_HATCHES[d], edgecolor="white",
                          linewidth=0.4, label=d)
            for d in ["ABA", "BAB"]
        ]
        legend_below(fig, handles, ["ABA", "BAB"], ncol=2,
                     title="Direction", y=-0.04)
        fig.suptitle(
            f"{translator_display_name(translator)} — round-trip asymmetry "
            f"(ABA vs BAB)"
        )
        fig.tight_layout()
        savefig(fig, output_dir / f"roundtrip_{translator}.png")


# --------------------------------------------------------------------------- #
# Directional asymmetry heatmap                                               #
# --------------------------------------------------------------------------- #

def _asymmetry_frame(rt_df: pd.DataFrame) -> pd.DataFrame:
    """Long frame of |ABA cosine − BAB cosine| per (translator, language)."""
    rows: list[dict] = []
    for translator in TRANSLATOR_ORDER:
        sub = rt_df[rt_df["translator"] == translator]
        if sub.empty:
            continue
        grp = sub.groupby(["language", "direction"])["cosine"].mean().reset_index()
        for lang in sorted(sub["language"].unique()):
            aba = grp[(grp["language"] == lang) & (grp["direction"] == "ABA")]["cosine"]
            bab = grp[(grp["language"] == lang) & (grp["direction"] == "BAB")]["cosine"]
            if aba.empty or bab.empty:
                continue
            rows.append({
                "translator": translator,
                "language":   lang,
                "asymmetry":  round(abs(aba.values[0] - bab.values[0]), 4),
            })
    return pd.DataFrame(rows)


def _draw_asymmetry(pivot: pd.DataFrame, title: str, path: Path,
                    width: float) -> None:
    cbar_label = "|ABA − BAB| cosine"
    fig, ax = plt.subplots(figsize=(width, max(2.0, len(pivot) * 0.30 + 1.3)))
    sns.heatmap(
        pivot, ax=ax, cmap=CMAP_INTENSITY, annot=True, fmt=".3f",
        annot_kws={"fontsize": 6.5},
        linewidths=0.4, linecolor="white",
        cbar_kws={"label": cbar_label, "pad": 0.03},
    )
    ax.set_title(title)
    ax.set_xlabel("")
    ax.set_ylabel("Language")
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
    style_heatmap_axes(ax, cbar_label=cbar_label)
    fig.tight_layout()
    savefig(fig, path)


def plot_asymmetry_heatmap(rt_df: pd.DataFrame, output_dir: str | Path) -> None:
    """
    |ABA cosine − BAB cosine| per language.

    Emits a combined heatmap with one column per system, plus a per-system
    heatmap for each. Rows are ordered by mean asymmetry across whichever
    systems are present, so the ordering does not depend on which backend
    happens to be loaded first.
    """
    output_dir = Path(output_dir)
    frame = _asymmetry_frame(rt_df)
    if frame.empty:
        return

    order = (frame.groupby("language")["asymmetry"].mean()
                  .sort_values(ascending=False).index.tolist())

    # ---- combined -------------------------------------------------------- #
    wide = (frame.pivot(index="language", columns="translator", values="asymmetry")
                 .reindex(index=order))
    wide = wide[[t for t in TRANSLATOR_ORDER if t in wide.columns]]
    wide.columns = [translator_display_name(t) for t in wide.columns]
    _draw_asymmetry(
        wide,
        "Directional asymmetry |ABA − BAB| (cosine)",
        output_dir / "asymmetry_heatmap.png",
        width=WIDTH_1COL * (1.0 + 0.35 * len(wide.columns)),
    )

    # ---- one per system --------------------------------------------------- #
    for translator in [t for t in TRANSLATOR_ORDER if t in frame["translator"].unique()]:
        one = (frame[frame["translator"] == translator]
               .pivot(index="language", columns="translator", values="asymmetry")
               .reindex(index=order))
        one.columns = [translator_display_name(translator)]
        _draw_asymmetry(
            one,
            f"{translator_display_name(translator)} — directional asymmetry\n"
            "|ABA − BAB| (cosine)",
            output_dir / f"asymmetry_heatmap_{translator}.png",
            width=WIDTH_1COL * 1.15,
        )
