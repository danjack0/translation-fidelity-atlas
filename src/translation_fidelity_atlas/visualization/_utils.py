"""
Shared figure-saving utilities.

Every plotting module in this package writes its output through
:func:`savefig`, which centralizes the DPI, layout, and directory handling.
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

# Headless rendering for servers / CI. Swap to "TkAgg" for interactive use.
matplotlib.use("Agg")
sns.set_theme(style="whitegrid", font_scale=1.05)

log = logging.getLogger(__name__)


def savefig(fig, path: str | Path, dpi: int = 160) -> None:
    """Save a figure with project-standard DPI and bbox handling."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    log.info("  Saved: %s", path)
