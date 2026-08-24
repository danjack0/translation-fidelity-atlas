#!/usr/bin/env python3
"""
Regenerate every figure from the saved result CSVs, for every backend present.

Does not call any translator — purely consumes the CSVs in ``data/results/``
and writes PNGs to ``figures/``. Safe to run repeatedly.

The defaults cover both translation systems: the combined long CSV drives the
per-backend and cross-backend figures, and the chain / round-trip inputs are
lists that are concatenated, so Google and NLLB-200 both appear.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from translation_fidelity_atlas.visualization import (  # noqa: E402
    DEFAULT_CHAIN_CSVS,
    DEFAULT_LONG_CSV,
    DEFAULT_ROUNDTRIP_CSVS,
    run_all,
)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--long-csv", default=DEFAULT_LONG_CSV,
                   help="(default: %(default)s — both backends)")
    p.add_argument("--chain-csv", nargs="*", default=list(DEFAULT_CHAIN_CSVS),
                   help="one or more telephone-chain CSVs, concatenated "
                        "(default: both backends)")
    p.add_argument("--roundtrip-csv", nargs="*", default=list(DEFAULT_ROUNDTRIP_CSVS),
                   help="one or more round-trip CSVs, concatenated "
                        "(default: both backends)")
    p.add_argument("--output-dir", default="figures")
    args = p.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    run_all(
        long_csv=args.long_csv,
        chain_csv=args.chain_csv,
        roundtrip_csv=args.roundtrip_csv,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
