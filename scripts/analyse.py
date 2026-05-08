#!/usr/bin/env python3
"""
Print summary statistics, ANOVA tables, and best/worst cells from the
back-translation results.

Outputs to stdout in human-readable form and (optionally) writes a Markdown
table to ``docs/findings_auto.md`` for the documentation pipeline.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from translation_fidelity_atlas.analysis import (   # noqa: E402
    extreme_cells,
    one_way_anova,
    summary_by,
    variance_decomposition,
)


def _hr(title: str) -> None:
    print("\n" + "=" * 72)
    print("  " + title)
    print("=" * 72)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--long-csv", default="data/results/google/back_translation_long.csv")
    p.add_argument("--metric", default="bleu",
                   choices=("cosine", "bleu", "ter", "embedding"))
    args = p.parse_args()

    df = pd.read_csv(args.long_csv)
    metric = args.metric

    _hr(f"Summary by family — {metric}")
    print(summary_by(df, "family", metric).to_string())

    _hr(f"Summary by domain — {metric}")
    print(summary_by(df, "domain", metric).to_string())

    _hr(f"One-way ANOVA  family ~ {metric}")
    print(one_way_anova(df, "family", metric))

    _hr(f"One-way ANOVA  domain ~ {metric}")
    print(one_way_anova(df, "domain", metric))

    _hr(f"Variance decomposition — {metric}")
    print(variance_decomposition(df, metric).to_string(index=False))

    _hr(f"Best / worst (language × domain) cells — {metric}")
    cells = extreme_cells(df, metric, n=5)
    print("BEST:");  print(cells["best"].to_string(index=False))
    print("\nWORST:"); print(cells["worst"].to_string(index=False))


if __name__ == "__main__":
    main()
