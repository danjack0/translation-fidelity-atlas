"""
Per-family heatmaps: language × domain grids of metric values.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from ..config import DOMAIN_ORDER, family_display_name
from ._utils import savefig


def plot_family_heatmaps(df: pd.DataFrame, output_dir: str | Path) -> None:
    """
    For each (translator × family), draw a 1×4 panel of heatmaps for the four
    primary metrics. Languages on the y-axis, domains on the x-axis.
    """
    output_dir = Path(output_dir)

    for (translator, family), sub in df.groupby(["translator", "family"]):
        languages = sub["language"].drop_duplicates().tolist()
        if len(languages) == 0:
            continue

        domains = [d for d in DOMAIN_ORDER if d in sub["domain"].unique()]

        def _matrix(metric: str) -> pd.DataFrame:
            return (
                sub.pivot_table(index="language", columns="domain",
                                values=metric, aggfunc="mean")
                .reindex(index=languages, columns=domains)
            )

        cos_df = _matrix("cosine")
        bleu_df = _matrix("bleu")
        ter_df = _matrix("ter")
        emb_df = _matrix("embedding")

        fig, axes = plt.subplots(1, 4, figsize=(25, max(4, len(languages) * 0.5 + 1)))

        sns.heatmap(cos_df,  annot=True, fmt=".3f", cmap="YlGnBu",
                    vmin=0.9, vmax=1.0, ax=axes[0])
        axes[0].set_title("Cosine Similarity (lexical)")

        sns.heatmap(bleu_df, annot=True, fmt=".1f", cmap="YlGnBu",
                    vmin=40, vmax=90, ax=axes[1])
        axes[1].set_title("BLEU")

        sns.heatmap(ter_df,  annot=True, fmt=".1f", cmap="YlOrRd_r",
                    ax=axes[2])
        axes[2].set_title("TER (lower = better)")
        axes[2].collections[0].colorbar.set_label("← better")

        sns.heatmap(emb_df,  annot=True, fmt=".3f", cmap="YlGnBu",
                    vmin=0.85, vmax=1.0, ax=axes[3])
        axes[3].set_title("Embedding Similarity (semantic)")

        for ax in axes:
            ax.set_xlabel("Domain")
            ax.set_ylabel("")
        axes[0].set_ylabel("Language")

        fig.suptitle(
            f"{family_display_name(family)}  —  {translator.capitalize()}",
            fontsize=14, fontweight="bold",
        )
        fig.tight_layout()
        savefig(fig, output_dir / f"heatmap_{translator}_{family}.png")
