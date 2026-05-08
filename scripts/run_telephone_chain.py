#!/usr/bin/env python3
"""
Run the telephone-chain experiment.

Each chain order (linguistic / reverse / random) is run for every domain.
Results are written to ``data/results/{translator}/telephone_chain.csv``.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from translation_fidelity_atlas.experiments import (          # noqa: E402
    load_corpora,
    run_all_chains,
)
from translation_fidelity_atlas.translators import get_translator  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--translator", default="google", choices=("google", "nllb"))
    p.add_argument("--nllb-model", default="facebook/nllb-200-distilled-600M")
    p.add_argument("--corpus-dir", default="data/corpora")
    p.add_argument("--cache",      default="data/translation_cache.json.gz")
    p.add_argument("--output",     default=None,
                   help="Default: data/results/{translator}/telephone_chain.csv")
    p.add_argument("--orders", nargs="*", default=None,
                   help="Subset of {linguistic, reverse, random}; all by default")
    args = p.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if args.translator == "nllb":
        tr = get_translator("nllb", model_name=args.nllb_model)
    else:
        tr = get_translator(args.translator)

    output = args.output or f"data/results/{tr.name}/telephone_chain.csv"
    corpora = load_corpora(args.corpus_dir)

    run_all_chains(
        domain_corpora=corpora,
        translators=[tr],
        cache_path=args.cache,
        output_csv=output,
        orders=args.orders,
    )


if __name__ == "__main__":
    main()
