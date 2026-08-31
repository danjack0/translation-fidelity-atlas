# Translation Fidelity Atlas

A **two-system**, multi-family, multi-domain back-translation fidelity
benchmark covering **45 languages across 8 typological families** and **6
content domains**, evaluated under three protocols (single-pivot
back-translation, five-hop telephone chains, and ABA/BAB directional
asymmetry) using **two translation systems** (Google Translate and NLLB-200)
and **four fidelity metrics** (cosine, BLEU, TER, sentence-transformer
embedding).

Both systems were run at **full parity**: the same 45 languages, the same 8
families, the same 6 domains, and all three protocols — 270 scored
(language × domain) cells per backend, 540 in total. NLLB-200 is not a side
experiment here; it is the control that tells us which findings are about
*language* and which are about *the translation system*.

This project asks one central question:

> When a sentence is translated into another language and back, what predicts
> how much it changes — the typological distance of the pivot language, or
> the linguistic register of the source text?

And, because there are two systems, a second one that turns out to matter more:

> Which of those answers survives when you swap the translation system out?

Every number below is re-derived from the committed CSVs and cache in
[`VERIFIED_FACTS.md`](VERIFIED_FACTS.md), which is the authority for this
README.

## TL;DR — headline findings

### What replicates across both systems

| Finding | Replicates? | Evidence |
|---|---|---|
| Family explains more BLEU variance than domain | **Yes** | η² 0.53 vs 0.16 (Google), 0.52 vs 0.18 (NLLB); all *p* < 1e-8 |
| The *ordering* of families | **Yes, strongly** | Spearman ρ = **+0.90** (*p* = 0.002) on family mean-BLEU ranks |
| East Asian is the worst family | **Yes** | Rank 8 of 8 under both backends |
| BLEU and cosine measure different things | **Yes, but weaker under NLLB** | Pearson *r* = 0.651 (Google) vs 0.761 (NLLB) |
| The *ordering* of domains | **No** | Spearman ρ = **+0.09** (*p* = 0.87) — indistinguishable from zero |
| "Technical is the best domain" | **No — reverses** | 1st (72.71) under Google, 5th of 6 (39.04) under NLLB |
| "Emotional is the worst domain" | **No — reverses** | 6th/worst (59.92) under Google, 3rd (44.05) under NLLB |

Derivations: [VERIFIED_FACTS §7](VERIFIED_FACTS.md#7-do-google-and-nllb-agree-on-the-headline-findings).

### Per-backend numbers

Every row is reported separately for each backend; no cell in this table is
cross-system. All BLEU means are over the 270 (language × domain) cells of
that backend.

| Question | Google Translate | NLLB-200 |
|---|---|---|
| Which factor explains more BLEU variance? | **Family** η² = 0.53 over **domain** η² = 0.16 — a 3.33× ratio | **Family** η² = 0.52 over **domain** η² = 0.18 — a 2.88× ratio |
| Best round-trip family | **Germanic**, mean BLEU 74.36 (da/no/sv all > 85 on technical text) | **Romance**, mean BLEU 53.66 |
| Worst round-trip family | **East Asian**, mean BLEU 50.99 (gap to best: 23.37) | **East Asian**, mean BLEU 30.18 (gap to best: 23.48) |
| Best content domain | **Technical**, mean BLEU 72.71 | **Conversational**, mean BLEU 49.82 |
| Worst content domain | **Emotional**, mean BLEU 59.92 | **Legal**, mean BLEU 35.43 |
| Highest-fidelity single cell | Danish technical, BLEU 86.78 | Norwegian conversational, BLEU 63.97 |
| Most degraded single cell | Thai legal, BLEU 39.99 | Croatian legal, BLEU 7.19 † |
| Do BLEU and cosine agree? | **No** — Pearson *r* = 0.651 (42% shared variance) | **Not really** — *r* = 0.761 (58% shared variance) |
| Overall mean BLEU | 64.96 | 42.70 |

† Croatian legal at BLEU 7.19 sits far below NLLB's next-worst cell (Croatian
technical, 14.08) and is flagged as a possible data-quality issue, not a
diagnosed result — see
[VERIFIED_FACTS §6](VERIFIED_FACTS.md#6-recomputed-statistics-per-backend).

The absolute-level gap between the columns is expected and is not the finding:
`nllb-200-distilled-600M` is a 600M-parameter distilled research model, Google
Translate is a production system. Translator identity alone accounts for
η² = 0.546 of pooled BLEU variance (*F* = 646.37, *p* = 3.0e-94). What is worth
reading is the *ordering* within each column.

## Typology travels. Domain difficulty belongs to the system.

This is the result the two-system design buys, and it splits cleanly in two.

**Typological structure is system-independent.** Family dominates domain on
BLEU under both backends (η² 0.53/0.16 for Google, 0.52/0.18 for NLLB — a 3.33×
and 2.88× ratio respectively, every *p* < 1e-8), and the family *ranking* itself
transfers almost intact: Spearman ρ = **+0.90** (*p* = 0.002). East Asian is
worst under both, Turkic second-worst under both, and Germanic and Romance are
the top two under both (they swap places). The only material movement is Slavic
and South & SE Asian trading 4th and 5th — 0.16 BLEU apart under NLLB, which is
noise. Two systems with entirely different architectures, training data, and
scale agree about which language families are hard to round-trip through.
That agreement is the strongest claim this repository makes
([§7a](VERIFIED_FACTS.md#7a-does-family-still-dominate-domain-for-nllb--yes)).

**Domain difficulty is not.** The domain ranking does not transfer at all:
Spearman ρ = **+0.09**, *p* = 0.87 — statistically indistinguishable from zero.
The reversals are large and they hit exactly the domains a Google-only reading
would have made the headline:

| Domain | Google rank (mean BLEU) | NLLB rank (mean BLEU) | Movement |
|---|---|---|---|
| technical | **1 — best (72.71)** | **5 (39.04)** | ▼ 4 — reverses |
| conversational | 2 (64.49) | **1 — best (49.82)** | ▲ 1 |
| idiomatic | 3 (64.37) | 2 (44.81) | ▲ 1 |
| legal | 4 (64.21) | **6 — worst (35.43)** | ▼ 2 |
| cultural | 5 (64.05) | 4 (43.06) | ▲ 1 |
| emotional | **6 — worst (59.92)** | 3 (44.05) | ▲ 3 — reverses |

Technical text — the domain Google round-trips best, by 8 BLEU points over its
nearest rival — takes the single largest backend penalty of any domain
(−33.67 BLEU) and lands 5th under NLLB. Emotional text goes the other way,
from worst to third-best. Under Google, four of the six domains sit inside a
0.5-point band (64.05–64.49: conversational, idiomatic, legal, cultural) while
technical sits far above and emotional below; under NLLB that structure is
simply gone, replaced by a different one
([§7c](VERIFIED_FACTS.md#7c-where-they-disagree--the-domain-finding-does-not-replicate)).

**The technical prediction was made in advance.** The corpus generation
specification ([docs/corpus_spec.md](docs/corpus_spec.md)), written before any
translation ran, states that technical text 'is expected to score highest in
back-translation fidelity because technical vocabulary is often borrowed across
languages or has established equivalents.' That expectation is confirmed under
Google (1st of 6, 72.71 BLEU) and refuted under NLLB (5th of 6, 39.04). The
reversal is therefore not a post-hoc reading of the data: the hypothesis was
recorded, one system met it, and the other did not.

**Read that as a finding, not a failure.** Typological distance is a property
of the language pair, and it shows up in any system that has to cross it.
Register difficulty is a property of what a given system was trained to
handle — whatever makes technical terminology come back word-for-word under
Google (the data do not say what; strong named-entity and terminology handling
is the obvious guess) plainly does not carry over to a distilled 600M research
model. A single-system benchmark cannot tell those two things apart.
Which means: **any domain-level claim about round-trip fidelity needs the name
of the MT system attached to it**, and every domain-level claim in this README
carries one.

**Form and meaning still come apart — in both systems.** BLEU (surface form)
and cosine similarity (closer to meaning) correlate but do not agree:
Pearson *r* = 0.651 under Google and 0.761 under NLLB, so 42% and 58% shared
variance respectively. The divergence is real in both and roughly **half as
large under NLLB** — NLLB's two metrics are substantially more aligned. The
same pattern shows in how the two metrics rank domains: Kendall τ = −0.067
under Google (near-total disagreement) but +0.467 under NLLB (moderate
agreement)
([§7b](VERIFIED_FACTS.md#7b-is-the-bleu-vs-cosine-divergence-present-in-both--yes-but-weaker-in-nllb)).

The cleanest single illustration is **emotional text under Google**: it is
simultaneously Google's *worst* BLEU domain (59.92) and its *best* cosine
domain (0.9887). The words come back different; the meaning comes back intact.
Conversational text behaves the same way, and the "emotional and conversational
preserve meaning best" half of that observation is the one part of the
form/meaning story that holds under both backends — Google's cosine top two are
emotional (0.9887) and conversational (0.9886), NLLB's are conversational
(0.9830) and emotional (0.9801). Note that idiomatic text is *not* an example
of failure in both form and meaning: it is second-worst on Google's cosine
(0.9809, above only cultural at 0.9801) but **third-best on Google's BLEU**
(64.37), so it does not fail in form at all
([§7d](VERIFIED_FACTS.md#7d-a-readme-claim-that-is-wrong-for-both-backends)).

**One scope caveat on "family dominates."** That result is a *surface-form*
result. On BLEU and TER it holds for both backends, but it inverts on one
semantic metric in each: under Google's sentence-transformer embedding, domain
wins (η² 0.557 vs family 0.192), and under NLLB's spaCy cosine, domain wins
(η² 0.521 vs family 0.189). "Family explains more variance than domain" is true
of how much the *wording* changes, not of how much the *meaning* changes
([§6](VERIFIED_FACTS.md#6-recomputed-statistics-per-backend)).

## Repository layout

```
translation-fidelity-atlas/
├── src/translation_fidelity_atlas/
│   ├── config.py             # families, domains, metrics, palette
│   ├── translators/          # Google + NLLB-200 backends, shared cache
│   ├── scoring/              # cosine / BLEU / TER / embedding
│   ├── experiments/          # back-translation, chain, round-trip
│   ├── visualization/        # all figure-generating code
│   └── analysis/             # ANOVA, effect sizes, summary tables
├── scripts/                  # CLI entrypoints (run_*, make_figures, analyse)
│   └── audit_*.py            # read-only re-derivations behind VERIFIED_FACTS.md
├── data/
│   ├── corpora/              # 6 × 100 sentence corpora
│   ├── results/
│   │   ├── google/
│   │   │   ├── back_translation_long.csv    # 270 rows
│   │   │   ├── back_translation_wide.csv    # 45 rows
│   │   │   ├── telephone_chain.csv          # 108 rows
│   │   │   ├── round_trip.csv               # 60 rows
│   │   │   └── per_family/{family}.csv      # 8 checkpoints
│   │   ├── nllb/
│   │   │   ├── back_translation_long.csv    # 270 rows
│   │   │   ├── back_translation_wide.csv    # 45 rows
│   │   │   ├── telephone_chain.csv          # 108 rows
│   │   │   ├── round_trip.csv               # 60 rows
│   │   │   └── per_family/{family}.csv      # 8 checkpoints
│   │   └── combined_long.csv                # 540 rows (google + nllb)
│   └── translation_cache.json.gz            # 141,088 unique cached
│                                            # translations, 8.09 MB gzipped
├── docs/
│   ├── methodology.md        # detailed methodology
│   ├── findings.md           # extended results writeup
│   └── nllb_setup.md         # how to run the local NLLB-200 backend
├── figures/                  # 52 PNG outputs, 300 dpi
└── VERIFIED_FACTS.md         # artifact-level audit of every claim above
```

## Quick start

```bash
git clone https://github.com/danjack0/translation-fidelity-atlas.git
cd translation-fidelity-atlas
python -m venv .venv && source .venv/bin/activate
pip install -e .
python -m spacy download en_core_web_md
```

Regenerate all 52 figures from the committed result CSVs (consumes CSVs only —
calls no translator). The defaults cover **both** systems and all three
protocols, so the bare command reproduces the committed figure set:

```bash
python scripts/make_figures.py
```

To restrict the run to one backend, point the inputs at that backend's CSVs:

```bash
python scripts/make_figures.py \
    --long-csv      data/results/google/back_translation_long.csv \
    --chain-csv     data/results/google/telephone_chain.csv \
    --roundtrip-csv data/results/google/round_trip.csv
```

Print summary statistics and ANOVA tables (also Google by default — point
`--long-csv` at the backend you want):

```bash
python scripts/analyse.py --metric bleu
python scripts/analyse.py --metric bleu --long-csv data/results/nllb/back_translation_long.csv
```

## Reproducing the experiments

All three protocols ran for **both** backends. Each runner takes
`--translator {google,nllb}`:

### Google Translate

```bash
python scripts/run_back_translation.py --translator google
python scripts/run_telephone_chain.py  --translator google
python scripts/run_round_trip.py       --translator google
```

### NLLB-200

NLLB-200 is a research model from Meta (`facebook/nllb-200-distilled-600M`),
run **locally** — no rate limits, but it needs ~3 GB of disk and either a GPU
or patience.

```bash
pip install -e .[nllb]
python scripts/run_back_translation.py --translator nllb
python scripts/run_telephone_chain.py  --translator nllb
python scripts/run_round_trip.py       --translator nllb
```

See [`docs/nllb_setup.md`](docs/nllb_setup.md) for hardware notes and what to
expect on CPU vs. GPU vs. Apple Silicon.

### The cache

`data/translation_cache.json.gz` holds **141,088 unique cached translations**
(8.09 MB gzipped) — 69,962 attributable to the Google run and 71,126 to the
NLLB run, with zero overlap, because the backend name is part of the MD5 key
preimage.

That is a count of distinct cached entries — `len(cache)` — not a count of
translation operations. The three protocols across both backends imply
**162,000** translation operations; the cache stores fewer entries than that
because the protocols reuse each other's work (round-trip's ABA leg re-uses
back-translation's forward and back pass, for instance).

Replaying all six backend × protocol combinations against the committed cache
produces **zero cache misses**, so re-running any experiment exactly as
committed costs **no API calls at all**. Misses occur only for cells you add —
a new language, a new domain, a new translator. Full derivation and the
per-protocol breakdown:
[VERIFIED_FACTS §1](VERIFIED_FACTS.md#1-unique-keys-in-datatranslation_cachejsongz)
and [§5](VERIFIED_FACTS.md#5-total-translations-and-whether-141088-is-defensible).

## What's in `data/`

| Path | Format | Description |
|---|---|---|
| `corpora/{domain}.txt` | text | Source sentences, one per line, 6 domains × exactly 100 sentences (600 total). |
| `results/google/back_translation_long.csv` | long | One row per (translator × language × domain), **270 rows**. Use this for Google plotting and analysis. |
| `results/google/back_translation_wide.csv` | wide | One row per (translator × language), 45 rows; all (domain × metric) cells as columns. |
| `results/google/telephone_chain.csv` | long | **108 rows** — 3 chain orders × 6 domains × 6 hops (hop 0 is a synthetic perfect baseline, so 5 hops are measured). |
| `results/google/round_trip.csv` | long | **60 rows** — 5 languages (`ar de es ja ru`) × 6 domains × 2 directions (ABA/BAB). |
| `results/google/per_family/{family}.csv` | wide | Per-family checkpoints written incrementally during the run; 8 files summing to 45 rows. |
| `results/nllb/back_translation_long.csv` | long | **270 rows** — identical schema and identical 45 × 6 coverage to the Google file. |
| `results/nllb/back_translation_wide.csv` | wide | 45 rows, as above. |
| `results/nllb/telephone_chain.csv` | long | **108 rows**, same 3 × 6 × 6 scope as Google. |
| `results/nllb/round_trip.csv` | long | **60 rows**, same 5 × 6 × 2 scope as Google. |
| `results/nllb/per_family/{family}.csv` | wide | 8 files summing to 45 rows. |
| `results/combined_long.csv` | long | **540 rows** — a straight concatenation of the two `back_translation_long.csv` files. Use this for cross-system analysis. |
| `translation_cache.json.gz` | gzipped JSON | MD5-keyed cache of every translation made, 141,088 entries / 8.09 MB; read by `experiments` modules transparently. |

Field-level documentation lives in [`data/README.md`](data/README.md).

## Methodology summary

* **Corpora.** Six register-distinct domains, each exactly 100 sentences:
  conversational, cultural, idiomatic, technical, legal, emotional. All
  English-source. See [`data/corpora`](data/corpora/) and
  [`docs/methodology.md`](docs/methodology.md) for the corpus design.
* **Languages.** 45 target languages distributed across 8 typological families
  (Romance 7, Germanic 7, Slavic 9, Semitic 3, East Asian 3, South & SE Asian
  9, Turkic 4, Uralic 3). Selection criteria: coverage in both backends,
  family representativeness, script diversity. Both backends cover the
  identical 45 languages — NLLB is not a subset.
* **Systems.** Google Translate (free endpoint) and NLLB-200
  (`facebook/nllb-200-distilled-600M`, pinned), run over the same corpora with
  the same protocols and the same scoring code.
* **Metrics.** Two surface-form metrics (BLEU and TER, via `sacrebleu`) and
  two semantic metrics (spaCy `en_core_web_md` cosine similarity on word
  vectors, and sentence-transformer cosine on `all-MiniLM-L6-v2` embeddings).
* **Statistics.** One-way ANOVA on each factor, η²-style variance
  decomposition, Pearson correlations between metrics, and Spearman rank
  correlations between backends.

## Limitations

* Single source language (English) — cross-source-language comparison is a
  natural extension.
* The free Google Translate endpoint changes silently, so absolute scores
  are time-stamped to the run date, not stable. The NLLB checkpoint is
  fixed and reproducible.
* The two systems are not matched in scale or purpose — a 600M distilled
  research model against a production service — so absolute score levels are
  not comparable between them (mean BLEU 64.96 vs 42.70). Only the *orderings*
  and *effect sizes* are compared here.
* **Domain-level results do not generalise across systems.** Everything this
  README says about which domain round-trips best or worst is a fact about a
  named backend, not about the text. See
  [§7c](VERIFIED_FACTS.md#7c-where-they-disagree--the-domain-finding-does-not-replicate).
* **Figure coverage is complete, but the asymmetry figure is dominated by two
  cells.** All three protocols are now visualised for both systems: the
  telephone-chain and round-trip figures exist per backend
  (`chain_degradation_{metric}_{google,nllb}.png`, `roundtrip_{google,nllb}.png`,
  `asymmetry_heatmap_{google,nllb}.png`) alongside two-system comparison
  versions, and `scatter_*` is split into per-backend panels so the Google panel
  reports its own *r* = 0.651 rather than the pooled 0.814 — the discrepancy
  [§8](VERIFIED_FACTS.md#8-figures) recorded is resolved. What remains: NLLB's
  directional asymmetry for Japanese (0.504) and Arabic (0.293) is one to two
  orders of magnitude larger than every other cell, so on a linear colour scale
  the entire Google column of `asymmetry_heatmap.png` reads as flat black. The
  annotations carry the exact values, and the Google differences being
  compressed there (0.000–0.020) are within noise, so no colour transform was
  applied to manufacture contrast between them.
* Domain corpora are LLM-generated against a fixed written specification
  ([docs/corpus_spec.md](docs/corpus_spec.md)) and spot-checked rather than
  reviewed line by line; they are not sampled from naturally occurring text. The
  spec fixes sentence length (8-25 words, target 12-18), requires one idea per
  sentence, and forbids cross-domain contamination (no idioms in the
  conversational set, no technical vocabulary outside the technical set). This
  buys comparability a natural corpus cannot: length and syntactic complexity are
  held roughly constant across domains, so a domain effect is unlikely to be a
  length effect in disguise. The cost is that domain boundaries are only as
  distinct as the spec made them. Since the domain effect is the finding that
  does *not* replicate across systems, this is the limitation most relevant to
  interpreting that result - a robustness check against externally constructed
  domain corpora (e.g. OPUS domain splits, where domain follows from provenance
  rather than from a prompt) is planned.

## License

Not uniform across the repository. Full text in [LICENSE](LICENSE).

**Code — MIT.** Everything in `src/`, `scripts/`, `docs/`, `tests/`, and the
project configuration.

**Corpora and results — MIT.** The 600 source sentences in `data/corpora/` are
author-created original text, and the CSVs in `data/results/` hold derived
metric values computed from them. Both are the author's own work.

**`data/translation_cache.json.gz` — not MIT.** The cache is machine-translation
output, so it is not the author's to relicense. Of its 141,088 unique cached
translations, **69,962 came from Google Translate** — use of that output is
subject to Google's Terms of Service — and **71,126 came from NLLB-200**, which
is released under **CC-BY-NC 4.0** and therefore permits **non-commercial
research use only**. The file is committed for reproducibility, so that the
published numbers can be checked without re-issuing 162,000 translation
operations against either system; it is not offered as a redistributable
translation dataset.

**Using this commercially?** The code, corpora, and results are yours under
MIT. The cache is not — delete it and regenerate it under your own licensed
access to a translation system using the runners in
[Reproducing the experiments](#reproducing-the-experiments).

## Citation

If you use this code or data, please cite:

```bibtex
@misc{jackson2026fidelity,
  title  = {Translation Fidelity Atlas: A two-system, multi-family,
            multi-domain back-translation benchmark},
  author = {Jackson, Daniel},
  year   = {2026},
  url    = {https://github.com/danjack0/translation-fidelity-atlas}
}
```
