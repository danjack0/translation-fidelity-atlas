"""Statistical analysis of fidelity results."""

from .statistics import (
    extreme_cells,
    one_way_anova,
    summary_by,
    variance_decomposition,
)

__all__ = [
    "summary_by",
    "one_way_anova",
    "variance_decomposition",
    "extreme_cells",
]
