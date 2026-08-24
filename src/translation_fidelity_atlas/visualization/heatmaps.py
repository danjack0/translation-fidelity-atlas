"""
Per-family heatmaps: language × domain grids of metric values.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from ..config import (
    DOMAIN_ORDER,
    METRIC_LABELS,
    family_display_name,
    metric_cbar_label,
    translator_display_name,
)
from .style import (
    WIDTH_2COL,
    metric_cmap,
    savefig,
    style_heatmap_axes,
)

#: Fixed colour ranges, so the same value reads as the same colour in every
#: family's panel and across both backends. Bounds were set from the observed
#: range over both systems (cosine 0.904–0.995, BLEU 7.2–86.8, TER 7.0–158.1,
#: embedding 0.624–0.985) rather than from Google alone: the previous BLEU
#: floor of 40 and embedding floor of 0.85 both sat *above* NLLB's minimum and
#: silently saturated its weakest cells to a single flat colour.
#:
#: TER is the one metric with a long tail (a single 158.1 cell against a 99th
#: percentile of 72), so its scale stops at 100 and the colorbar is drawn with
#: an "over" arrow. Annotations always print the true value regardless.
_VLIMS: dict[str, tuple[float, float]] = {
    "cosine":    (0.90, 1.00),
    "bleu":      (0.0, 90.0),
    "ter":       (0.0, 100.0),
    "embedding": (0.60, 1.00),
}

_EXTEND: dict[str, str] = {
    "cosine": "neither", "bleu": "neither", "ter": "max", "embedding": "neither",
}

_FMT: dict[str, str] = {
    "cosine": ".3f", "bleu": ".1f", "ter": ".1f", "embedding": ".3f",
}


def plot_family_heatmaps(df: pd.DataFrame, output_dir: str | Path) -> None:
    """
    For each (translator × family), draw a 2×2 panel of heatmaps for the four
    primary metrics. Languages on the y-axis, domains on the x-axis.

    The 2×2 arrangement replaces a 1×4 strip that was 25 inches wide: at any
    printable width that strip reduced its own annotations to illegibility.
    """
    output_dir = Path(output_dir)

    for (translator, family), sub in df.groupby(["translator", "family"]):
        languages = sub["language"].drop_duplicates().tolist()
        if len(languages) == 0:
            continue

        domains = [d for d in DOMAIN_ORDER if d in sub["domain"].unique()]

        def _matrix(metric: str, _sub=sub, _langs=languages, _doms=domains) -> pd.DataFrame:
            return (
                _sub.pivot_table(index="language", columns="domain",
                                 values=metric, aggfunc="mean")
                .reindex(index=_langs, columns=_doms)
            )

        metrics = ["cosine", "bleu", "ter", "embedding"]
        row_h = max(1.6, 0.22 * len(languages) + 1.15)
        fig, axes = plt.subplots(2, 2, figsize=(WIDTH_2COL, 2 * row_h))

        for ax, metric in zip(axes.ravel(), metrics):
            vmin, vmax = _VLIMS[metric]
            cbar_label = metric_cbar_label(metric)
            sns.heatmap(
                _matrix(metric), ax=ax,
                annot=True, fmt=_FMT[metric], annot_kws={"fontsize": 6.0},
                cmap=metric_cmap(metric), vmin=vmin, vmax=vmax,
                linewidths=0.4, linecolor="white",
                cbar_kws={"label": cbar_label, "pad": 0.02,
                          "extend": _EXTEND[metric]},
            )
            ax.set_title(METRIC_LABELS[metric])
            ax.set_xlabel("")
            ax.set_ylabel("")
            ax.set_xticklabels([t.get_text().capitalize() for t in ax.get_xticklabels()],
                               rotation=35, ha="right")
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
            style_heatmap_axes(ax, cbar_label=cbar_label)

        for ax in axes[:, 0]:
            ax.set_ylabel("Language")
        for ax in axes[1, :]:
            ax.set_xlabel("Domain")

        fig.suptitle(
            f"{family_display_name(family)} — {translator_display_name(translator)}"
        )
        fig.tight_layout()
        savefig(fig, output_dir / f"heatmap_{translator}_{family}.png")
