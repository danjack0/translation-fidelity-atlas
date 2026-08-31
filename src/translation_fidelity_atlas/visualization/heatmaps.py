"""
Language × domain heatmaps of metric values.

Two views of the same grid:

* :func:`plot_all_language_heatmap` — the overview. Every language at once,
  both systems side by side, one metric, rows banded by typological family.
* :func:`plot_family_heatmaps` — the granular appendix. One family at a time,
  all four metrics, every cell annotated with its value.
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.transforms import blended_transform_factory, offset_copy

from ..config import (
    DOMAIN_ORDER,
    FAMILY_ORDER,
    LANGUAGE_FAMILIES,
    METRIC_LABELS,
    METRIC_SHORT_LABELS,
    TRANSLATOR_ORDER,
    family_display_name,
    family_tick_label,
    metric_cbar_label,
    translator_display_name,
)
from .style import (
    CMAP_DIVERGING,
    WIDTH_1COL,
    WIDTH_2COL,
    metric_cmap,
    savefig,
    style_heatmap_axes,
)

log = logging.getLogger(__name__)


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


# --------------------------------------------------------------------------- #
# Full-coverage overview: every language, both systems, one metric            #
# --------------------------------------------------------------------------- #

#: Symmetric limit for the z-scored panels. 96.7% of the 540 cells fall within
#: ±2 and only one (NLLB Croatian, legal) falls outside ±3, so the scale stops
#: here and that cell is flagged with an arrow — the same treatment the TER
#: tail gets above. Stretching to ±3.5 to accommodate a single outlier bleaches
#: the banding the figure exists to show.
_Z_VLIM = 3.0

#: Rule between family blocks: a dark line inside a white halo, so the boundary
#: stays visible against both ends of viridis (dark purple and bright yellow).
_SEP_HALO: dict[str, object] = {"color": "white", "linewidth": 2.0, "zorder": 3}
_SEP_RULE: dict[str, object] = {"color": "#1A1A1A", "linewidth": 0.8, "zorder": 4}

#: Left-margin geometry for the family brackets, in points from the axes edge.
#: Points rather than axes fractions, so the gap does not change when the panel
#: is made narrower — what it has to clear is the language tick labels, and
#: those are type.
_BRACKET_OFFSET_PT = -24.0
_LABEL_OFFSET_PT = -29.0


def _family_row_order(df: pd.DataFrame) -> tuple[list[str], list[tuple[str, int, int]]]:
    """
    Language rows in typological-family order, plus the band each family spans.

    Returns ``(languages, bands)``, where ``bands`` holds ``(family, start,
    stop)`` half-open row-index ranges. Families follow :data:`FAMILY_ORDER`
    and, within a family, languages follow the order they are declared in
    :data:`LANGUAGE_FAMILIES`. Never alphabetical: sorting rows by name
    interleaves the families and destroys the banding that is the entire point
    of this figure.
    """
    present = set(df["language"].unique())
    families = FAMILY_ORDER + [f for f in LANGUAGE_FAMILIES if f not in FAMILY_ORDER]

    languages: list[str] = []
    bands: list[tuple[str, int, int]] = []
    for family in families:
        block = [lang for lang in LANGUAGE_FAMILIES[family] if lang in present]
        if not block:
            continue
        bands.append((family, len(languages), len(languages) + len(block)))
        languages.extend(block)

    unclassified = sorted(present - set(languages))
    if unclassified:
        log.warning("  %d language(s) absent from LANGUAGE_FAMILIES, appended as "
                    "a final band: %s", len(unclassified), ", ".join(unclassified))
        bands.append(("unclassified", len(languages),
                      len(languages) + len(unclassified)))
        languages.extend(unclassified)

    return languages, bands


def _draw_family_separators(ax, bands: list[tuple[str, int, int]]) -> None:
    """Horizontal rule at every internal family boundary."""
    for _family, start, _stop in bands[1:]:
        ax.axhline(start, **_SEP_HALO)
        ax.axhline(start, **_SEP_RULE)


def _draw_family_labels(ax, bands: list[tuple[str, int, int]]) -> None:
    """Bracket and name each family block in the left margin of ``ax``."""
    axes_x_data_y = blended_transform_factory(ax.transAxes, ax.transData)
    bracket = offset_copy(axes_x_data_y, fig=ax.figure,
                          x=_BRACKET_OFFSET_PT, y=0, units="points")

    for family, start, stop in bands:
        ax.plot([0, 0], [start + 0.15, stop - 0.15], transform=bracket,
                color="#3F3F3F", linewidth=0.9, solid_capstyle="butt",
                clip_on=False, zorder=5)
        ax.annotate(
            family_tick_label(family, width=10),
            xy=(0, (start + stop) / 2), xycoords=("axes fraction", "data"),
            xytext=(_LABEL_OFFSET_PT, 0), textcoords="offset points",
            ha="right", va="center", multialignment="right",
            fontsize=6.0, fontweight="bold", color="#1A1A1A",
            annotation_clip=False,
        )


def _draw_overview(
    panels: list[tuple[str, pd.DataFrame]],
    *,
    bands: list[tuple[str, int, int]],
    cmap: str,
    vmin: float,
    vmax: float,
    extend: str,
    cbar_label: str,
    title: str,
    subtitle: str,
    path: Path,
) -> None:
    """
    Render the shared two-panel layout: one heatmap per system, rows banded by
    family, and a single colorbar serving both panels.

    Both panels are drawn with ``cbar=False`` on identical ``vmin``/``vmax``;
    the one colorbar afterwards is what makes them directly comparable, and is
    also why no cell is annotated — 540 numbers at this row count are illegible
    at a single column's width, so the bar carries the scale instead.
    """
    n_rows = len(panels[0][1].index)

    # Sized in real inches at the printed width: portrait, one journal column.
    fig, axes = plt.subplots(1, len(panels),
                             figsize=(WIDTH_1COL, 0.128 * n_rows + 1.55))
    axes = np.atleast_1d(axes)
    left, right = 0.30, 0.855
    fig.subplots_adjust(left=left, right=right, top=0.905, bottom=0.055, wspace=0.10)

    for ax, (translator, matrix) in zip(axes, panels):
        sns.heatmap(
            matrix, ax=ax, cmap=cmap, vmin=vmin, vmax=vmax,
            annot=False, cbar=False, linewidths=0.3, linecolor="white",
        )
        ax.set_title(translator_display_name(translator), fontsize=7.5)
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.set_xticklabels([t.get_text().capitalize() for t in ax.get_xticklabels()],
                           rotation=45, ha="right", fontsize=6.0)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=6.0)
        style_heatmap_axes(ax)
        _draw_family_separators(ax, bands)

    # Language codes and family brackets on the leftmost panel only — every
    # other panel is the same rows in the same order.
    for ax in axes[1:]:
        ax.tick_params(labelleft=False)
    _draw_family_labels(axes[0], bands)

    cax = fig.add_axes([0.885, 0.30, 0.028, 0.34])
    fig.colorbar(axes[0].collections[0], cax=cax, extend=extend)
    # style_heatmap_axes reaches the colorbar through the mappable that now
    # owns it, so the bar picks up the same styling as every other heatmap.
    style_heatmap_axes(axes[0], cbar_label=cbar_label)

    # Both anchored va="bottom" and centred on the panel block rather than on
    # the figure, whose left margin is all family labels: a top-anchored
    # suptitle grows downwards into the subtitle.
    centre = (left + right) / 2
    fig.suptitle(title, x=centre, y=0.968, va="bottom")
    fig.text(centre, 0.945, subtitle, ha="center", va="bottom",
             fontsize=6.5, color="#555555")
    savefig(fig, path)


def plot_all_language_heatmap(df: pd.DataFrame, output_dir: str | Path,
                              metric: str = "bleu") -> None:
    """
    Every language × every domain, both systems side by side, for one metric.

    Emits two files:

    ``heatmap_all_languages_{metric}.png``
        Raw values on the project-wide fixed scale for the metric, shared
        across both panels. Directly comparable cell for cell, which is what
        makes NLLB-200's uniformly lower absolute level legible.

    ``heatmap_all_languages_{metric}_zscored.png``
        The same layout, each panel standardised against its own mean and SD.
        The shared raw scale costs NLLB most of its dynamic range; z-scoring
        buys it back, so within-system structure — which families a system is
        relatively weak on — reads at equal strength in both panels. These are
        signed values about a meaningful zero, so this one takes the diverging
        map rather than the sequential one.

    Rows are ordered by typological family with a rule drawn between families.
    That is the whole design: the banding is meant to be visible without
    running a single test. :func:`plot_family_heatmaps` remains the granular,
    per-cell-annotated view.
    """
    output_dir = Path(output_dir)

    languages, bands = _family_row_order(df)
    domains = [d for d in DOMAIN_ORDER if d in df["domain"].unique()]
    translators = [t for t in TRANSLATOR_ORDER if t in df["translator"].unique()]
    if not (languages and domains and translators):
        log.warning("  Skipping full-coverage heatmap — no rows to plot")
        return

    panels = [
        (translator,
         df[df["translator"] == translator]
         .pivot_table(index="language", columns="domain", values=metric, aggfunc="mean")
         .reindex(index=languages, columns=domains))
        for translator in translators
    ]

    n_lang, n_dom = len(languages), len(domains)
    short = METRIC_SHORT_LABELS[metric]
    grid = f"{n_lang} languages × {n_dom} domains"

    # ---- raw values, one scale shared by both panels ---------------------- #
    vmin, vmax = _VLIMS[metric]
    _draw_overview(
        panels, bands=bands, cmap=metric_cmap(metric),
        vmin=vmin, vmax=vmax, extend=_EXTEND[metric],
        cbar_label=metric_cbar_label(metric),
        title=f"Back-translation {short}",
        subtitle=f"{grid} · rows grouped by family · shared colour scale",
        path=output_dir / f"heatmap_all_languages_{metric}.png",
    )

    # ---- z-scored within each panel --------------------------------------- #
    z_panels: list[tuple[str, pd.DataFrame]] = []
    for translator, matrix in panels:
        values = matrix.to_numpy(dtype=float)
        sd = float(np.nanstd(values, ddof=0))
        z_panels.append((translator,
                         (matrix - float(np.nanmean(values))) / sd if sd
                         else matrix * 0.0))

    low = min(float(np.nanmin(z.to_numpy())) for _, z in z_panels)
    high = max(float(np.nanmax(z.to_numpy())) for _, z in z_panels)
    z_extend = ("both" if low < -_Z_VLIM and high > _Z_VLIM
                else "min" if low < -_Z_VLIM
                else "max" if high > _Z_VLIM
                else "neither")

    _draw_overview(
        z_panels, bands=bands, cmap=CMAP_DIVERGING,
        vmin=-_Z_VLIM, vmax=_Z_VLIM, extend=z_extend,
        cbar_label=f"{short} z-score within panel",
        title=f"Back-translation {short} (z-scored)",
        subtitle=f"{grid} · 0 = that system's own mean",
        path=output_dir / f"heatmap_all_languages_{metric}_zscored.png",
    )


# --------------------------------------------------------------------------- #
# Per-family detail                                                           #
# --------------------------------------------------------------------------- #


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
