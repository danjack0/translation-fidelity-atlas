"""
The single source of figure styling for this project.

Every plotting module imports from here and nowhere else sets rcParams, picks a
colormap, chooses a font size, or calls ``savefig``. Importing this module
applies the style; call :func:`apply_style` again to reassert it if something
downstream (notably seaborn) has overwritten rcParams.

Design targets
--------------
* **Two-column layout.** Figures are sized in real inches at the width they
  will be printed — :data:`WIDTH_1COL` for a single column, :data:`WIDTH_2COL`
  for a full-width figure — so an 8 pt label is genuinely 8 pt on the page
  rather than 8 pt shrunk by an arbitrary downscale.
* **300 dpi minimum**, tight bounding box, no clipping.
* **No chartjunk.** Top and right spines off, gridlines on the value axis only.
* **Perceptually uniform colormaps only.** No jet, no rainbow.
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

from ..config import METRIC_HIGHER_IS_BETTER

# Headless rendering for servers / CI. Swap to "TkAgg" for interactive use.
matplotlib.use("Agg")

log = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Canvas geometry                                                             #
# --------------------------------------------------------------------------- #

#: Width of one column in a two-column layout, inches.
WIDTH_1COL = 3.4
#: Width of a figure spanning both columns, inches.
WIDTH_2COL = 7.0

#: Publication raster density. Everything is written at this dpi.
DPI = 300


# --------------------------------------------------------------------------- #
# Colormaps — perceptually uniform only                                       #
# --------------------------------------------------------------------------- #

#: Sequential, for metrics where a higher value is better.
CMAP_SEQ = "viridis"
#: Sequential reversed, for metrics where a lower value is better (TER), so
#: that the bright end of the bar always means "better" across a panel row.
CMAP_SEQ_R = "viridis_r"
#: Sequential, for magnitude-of-effect grids that have no "good" direction.
CMAP_INTENSITY = "magma"
#: Diverging, for correlations on [-1, 1]. Moreland's smooth cool-warm map:
#: monotonic in lightness away from the neutral centre, and CVD-safe.
CMAP_DIVERGING = "coolwarm"


def metric_cmap(metric: str) -> str:
    """Sequential colormap for a metric, oriented so bright always means better."""
    return CMAP_SEQ if METRIC_HIGHER_IS_BETTER.get(metric, True) else CMAP_SEQ_R


# --------------------------------------------------------------------------- #
# rcParams                                                                    #
# --------------------------------------------------------------------------- #

RC_PARAMS: dict[str, object] = {
    # -- output ----------------------------------------------------------- #
    "figure.dpi":          DPI,
    "savefig.dpi":         DPI,
    "savefig.bbox":        "tight",
    "savefig.pad_inches":  0.03,
    "figure.facecolor":    "white",
    "savefig.facecolor":   "white",

    # -- type ------------------------------------------------------------- #
    # Sizes are absolute points at the printed width, not scaled.
    "font.family":         "sans-serif",
    "font.sans-serif":     ["DejaVu Sans", "Arial", "Helvetica", "sans-serif"],
    "font.size":           8.0,
    "axes.titlesize":      9.0,
    "axes.titleweight":    "bold",
    "axes.titlepad":       5.0,
    "axes.labelsize":      8.0,
    "xtick.labelsize":     7.0,
    "ytick.labelsize":     7.0,
    "legend.fontsize":     7.0,
    "legend.title_fontsize": 7.5,
    "figure.titlesize":    10.0,
    "figure.titleweight":  "bold",
    # Use a real minus sign, and keep maths in the same face as the prose.
    "axes.unicode_minus":  True,
    "mathtext.default":    "regular",

    # -- chartjunk removal ------------------------------------------------- #
    "axes.spines.top":     False,
    "axes.spines.right":   False,
    "axes.edgecolor":      "#3F3F3F",
    "axes.linewidth":      0.7,
    "axes.grid":           True,
    "axes.grid.axis":      "y",       # value axis only; category axis has none
    "axes.axisbelow":      True,
    "grid.color":          "#DBDBDB",
    "grid.linewidth":      0.5,
    "grid.alpha":          1.0,
    "legend.frameon":      False,
    "legend.handlelength": 1.6,
    "legend.columnspacing": 1.2,
    "legend.handletextpad": 0.5,

    # -- ticks ------------------------------------------------------------- #
    "xtick.color":         "#3F3F3F",
    "ytick.color":         "#3F3F3F",
    "xtick.direction":     "out",
    "ytick.direction":     "out",
    "xtick.major.width":   0.7,
    "ytick.major.width":   0.7,
    "xtick.major.size":    2.5,
    "ytick.major.size":    2.5,

    # -- marks ------------------------------------------------------------- #
    "lines.linewidth":     1.4,
    "lines.markersize":    4.0,
    "patch.linewidth":     0.5,
    "patch.edgecolor":     "#FFFFFF",
    "image.cmap":          CMAP_SEQ,
    "errorbar.capsize":    2.0,
}


def apply_style() -> None:
    """Apply the project style to matplotlib's global rcParams."""
    matplotlib.rcParams.update(RC_PARAMS)


apply_style()


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #

def style_axes(ax, *, grid_axis: str = "y") -> None:
    """
    Normalize one axes object after a library (seaborn, pandas) has drawn on it.

    ``grid_axis`` may be "y", "x", "both", or "none".
    """
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(0.7)
        ax.spines[side].set_color("#3F3F3F")
    if grid_axis == "none":
        ax.grid(False)
    else:
        ax.grid(False)
        ax.grid(True, axis=grid_axis, color="#DBDBDB", linewidth=0.5)
    ax.set_axisbelow(True)


def style_heatmap_axes(ax, cbar_label: str | None = None) -> None:
    """
    Normalize a seaborn heatmap: no spines, no grid, and a labelled colorbar.

    A colorbar without a label is an unreadable strip of colour, so every
    heatmap in this project passes one.
    """
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)
    if cbar_label is not None and ax.collections:
        cbar = ax.collections[0].colorbar
        if cbar is not None:
            cbar.set_label(cbar_label, fontsize=7.0)
            cbar.ax.tick_params(labelsize=6.5, length=2, width=0.6)
            cbar.outline.set_linewidth(0.5)
            cbar.outline.set_edgecolor("#BFBFBF")


def legend_below(fig, handles, labels, *, ncol: int, title: str | None = None,
                 y: float = 0.0) -> None:
    """Place a shared legend beneath the figure, outside the axes."""
    fig.legend(
        handles, labels, title=title, loc="upper center",
        bbox_to_anchor=(0.5, y), ncol=ncol, frameon=False,
    )


def savefig(fig, path: str | Path, dpi: int = DPI) -> None:
    """Save a figure at publication density with a tight bounding box."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    log.info("  Saved: %s", path)


__all__ = [
    "WIDTH_1COL", "WIDTH_2COL", "DPI",
    "CMAP_SEQ", "CMAP_SEQ_R", "CMAP_INTENSITY", "CMAP_DIVERGING",
    "metric_cmap", "apply_style", "style_axes", "style_heatmap_axes",
    "legend_below", "savefig", "RC_PARAMS",
]
