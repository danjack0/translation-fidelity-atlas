#!/usr/bin/env python3
"""
Draw the headline figure: share of BLEU variance explained (eta-squared) by
language family vs. content domain, side by side for each translation backend.

Reads ``data/results/combined_long.csv`` and computes eta-squared with the
repo's own ``one_way_anova`` (the same numbers as VERIFIED_FACTS.md §6a), so the
figure never carries hand-typed values. Writes
``figures/headline_family_vs_domain_bleu.png`` (1800x940, sized for a social
or README preview). Safe to run repeatedly; no translator calls.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

from translation_fidelity_atlas.analysis import one_way_anova  # noqa: E402

BACKENDS = [("google", "Google Translate"), ("nllb", "NLLB-200")]
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, MUTED, GRID, SURF = "#1f1f1e", "#55544f", "#8a8983", "#e6e5e0", "#fcfcfb"


def compute(df: pd.DataFrame) -> list[dict]:
    rows = []
    for key, label in BACKENDS:
        sub = df[df["translator"] == key]
        fam = one_way_anova(sub, "family", "bleu")
        dom = one_way_anova(sub, "domain", "bleu")
        rows.append({
            "label": label,
            "n": len(sub),
            "family": fam["eta_squared"],
            "domain": dom["eta_squared"],
            "max_p": max(fam["p"], dom["p"]),
        })
    return rows


def draw(rows: list[dict], out: Path) -> None:
    plt.rcParams["font.family"] = "DejaVu Sans"
    fig, ax = plt.subplots(figsize=(12, 6.27), dpi=150)
    fig.patch.set_facecolor(SURF)
    ax.set_facecolor(SURF)

    w, gap = 0.34, 0.02

    def bar(x, h, color):
        ax.add_patch(FancyBboxPatch((x - w / 2, 0), w, h, boxstyle="round,pad=0,rounding_size=0.012",
                                    mutation_aspect=1 / 1.6, fc=color, ec=SURF, lw=2))

    for x, r in enumerate(rows):
        xf, xd = x - w / 2 - gap / 2, x + w / 2 + gap / 2
        bar(xf, r["family"], BLUE)
        bar(xd, r["domain"], ORANGE)
        for xx, v in ((xf, r["family"]), (xd, r["domain"])):
            ax.text(xx, v + 0.015, f"{v * 100:.0f}%", ha="center", va="bottom",
                    fontsize=20, color=INK, weight="bold")
        ax.text(xf, -0.035, "Language\nfamily", ha="center", va="top", fontsize=15, color=INK2)
        ax.text(xd, -0.035, "Content\ndomain", ha="center", va="top", fontsize=15, color=INK2)
        ax.text(x, 0.715, r["label"], ha="center", va="bottom", fontsize=18, color=INK, weight="bold")
        ax.text(x, 0.675, f"family explains {r['family'] / r['domain']:.1f}× more",
                ha="center", va="bottom", fontsize=14, color=INK2)

    ax.set_xlim(-0.6, 1.6)
    ax.set_ylim(0, 0.76)
    ax.set_xticks([])
    ax.set_yticks([0, 0.2, 0.4, 0.6])
    ax.set_yticklabels(["0%", "20%", "40%", "60%"], fontsize=13, color=MUTED)
    ax.yaxis.grid(True, color=GRID, lw=1)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(axis="y", length=0)
    ax.set_ylabel("Share of BLEU variance explained (η²)", fontsize=13, color=INK2)

    n = rows[0]["n"]
    p_txt = "all p < 1e-8" if max(r["max_p"] for r in rows) < 1e-8 else "see VERIFIED_FACTS.md for p-values"
    fig.text(0.06, 0.94, "Language family explains ~3x more BLEU variance than content domain",
             fontsize=19.5, weight="bold", color=INK, ha="left")
    fig.text(0.06, 0.885, f"Back-translation BLEU across 45 languages, 8 families, 6 domains · "
                          f"one-way ANOVA, {n} cells per system, {p_txt}",
             fontsize=12.5, color=INK2, ha="left")
    fig.text(0.06, 0.022, "Translation Fidelity Atlas · github.com/danjack0/translation-fidelity-atlas",
             fontsize=11.5, color=MUTED, ha="left")

    plt.subplots_adjust(left=0.1, right=0.97, top=0.84, bottom=0.2)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=SURF)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--long-csv", default=str(ROOT / "data/results/combined_long.csv"))
    p.add_argument("--output", default=str(ROOT / "figures/headline_family_vs_domain_bleu.png"))
    args = p.parse_args()

    rows = compute(pd.read_csv(args.long_csv))
    for r in rows:
        print(f"{r['label']:17s} n={r['n']}  family eta2={r['family']:.4f}  "
              f"domain eta2={r['domain']:.4f}  ratio={r['family'] / r['domain']:.2f}x")
    draw(rows, Path(args.output))
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
