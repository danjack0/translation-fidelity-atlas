#!/usr/bin/env python3
"""
Regenerate every figure from the saved result CSVs.

Does not call any translator — purely consumes the CSVs in
``data/results/`` and writes PNGs to ``figures/``. Safe to run repeatedly.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from translation_fidelity_atlas.visualization import run_all  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--long-csv", default="data/results/google/back_translation_long.csv")
    p.add_argument("--chain-csv", default="data/results/google/telephone_chain.csv")
    p.add_argument("--roundtrip-csv", default="data/results/google/round_trip.csv")
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
