#!/usr/bin/env python3
"""
Run the back-translation experiment for one translator.

Examples
--------
    # Google Translate (default)
    python scripts/run_back_translation.py

    # NLLB-200, 1.3B variant on GPU
    python scripts/run_back_translation.py --translator nllb \\
        --nllb-model facebook/nllb-200-1.3B
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Allow ``python scripts/run_back_translation.py`` from a fresh checkout.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from translation_fidelity_atlas.config import LANGUAGE_FAMILIES   # noqa: E402
from translation_fidelity_atlas.experiments import (              # noqa: E402
    load_corpora,
    run_experiment,
)
from translation_fidelity_atlas.translators import get_translator # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--translator", default="google", choices=("google", "nllb"))
    p.add_argument("--nllb-model", default="facebook/nllb-200-distilled-600M",
                   help="HF model id (only used when --translator nllb)")
    p.add_argument("--corpus-dir", default="data/corpora")
    p.add_argument("--output-dir", default=None,
                   help="Default: data/results/{translator}/")
    p.add_argument("--cache",      default="data/translation_cache.json.gz")
    p.add_argument("--max-workers", type=int, default=4)
    args = p.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if args.translator == "nllb":
        tr = get_translator("nllb", model_name=args.nllb_model)
    else:
        tr = get_translator(args.translator)

    output_dir = Path(args.output_dir or f"data/results/{tr.name}")
    corpora = load_corpora(args.corpus_dir)

    run_experiment(
        domain_corpora=corpora,
        families=LANGUAGE_FAMILIES,
        translator=tr,
        cache_path=args.cache,
        output_dir=output_dir,
        max_workers=args.max_workers,
    )


if __name__ == "__main__":
    main()
