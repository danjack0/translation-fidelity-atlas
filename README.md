# Translation Fidelity Atlas

A multi-system, multi-family, multi-domain back-translation fidelity benchmark
covering **45 languages across 8 typological families** and **6 content
domains**, evaluated under three protocols (single-pivot back-translation,
five-hop telephone chains, and ABA/BAB directional asymmetry) using **two
translation systems** (Google Translate, NLLB-200) and **four fidelity
metrics** (cosine, BLEU, TER, sentence-transformer embedding).

This project asks one central question:

> When a sentence is translated into another language and back, what predicts
> how much it changes — the typological distance of the pivot language, or
> the linguistic register of the source text?

## TL;DR — Headline findings (Google Translate)

| Question | Answer |
|---|---|
| Which factor explains more variance in BLEU? | **Family** (η² = 0.53) over **domain** (η² = 0.16) — a 3.3× ratio. Both highly significant (*p* < 0.001). |
| Best round-trip family? | **Germanic** (mean BLEU 74.4) — Danish, Norwegian, Swedish all > 85 BLEU on technical text. |
| Worst round-trip family? | **East Asian** (mean BLEU 51.0). The full Germanic ↔ East Asian gap is 23 BLEU points. |
| Best content domain? | **Technical** (mean BLEU 72.7) — terminology and named entities are word-for-word stable. |
| Worst content domain? | **Emotional** (mean BLEU 59.9) — register-heavy, harder to round-trip. |
| Most degraded single cell? | Thai legal text — BLEU 40.0. |
| Highest-fidelity single cell? | Danish technical text — BLEU 86.8. |
| Do BLEU and cosine measure the same thing? | **No.** Pearson r = 0.651 — they correlate but disagree about which domains are "hardest". Form (BLEU) and meaning (cosine) come apart. |

The form-versus-meaning gap is the most interesting result. By BLEU, technical
text round-trips best; but by cosine similarity (which is more sensitive to
meaning than to surface form), the *most-preserved* domains are
**emotional** and **conversational**. Technical terminology survives
word-for-word; technical *meaning* doesn't survive any better than emotional
meaning does. Idiomatic and cultural text are the worst on both metrics —
they fail in form *and* meaning, the only domains that do.

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
├── scripts/                  # CLI entrypoints (run, make_figures, analyse)
├── data/
│   ├── corpora/              # 6 × 100 sentence corpora
│   ├── results/google/       # back-translation results CSVs
│   └── translation_cache.json.gz   # 54k cached translations (3 MB gzipped)
├── docs/
│   ├── methodology.md        # detailed methodology
│   ├── findings.md           # extended results writeup
│   └── nllb_setup.md         # how to run the local NLLB-200 backend
└── figures/                  # PNG outputs of every plot
```

## Quick start

```bash
git clone https://github.com/danjackdev/translation-fidelity-atlas.git
cd translation-fidelity-atlas
python -m venv .venv && source .venv/bin/activate
pip install -e .
python -m spacy download en_core_web_md
```

Regenerate every figure from the committed result CSVs (no API calls,
~30 seconds):

```bash
python scripts/make_figures.py
```

Print summary statistics and ANOVA tables:

```bash
python scripts/analyse.py --metric bleu
```

## Reproducing the experiments

The committed `data/translation_cache.json.gz` holds 54,025 translations from
the Google run, so re-running the experiment hits the API only for cells you
add (a new language, a new domain, a new translator). Cache hits are
free; cache misses are ~0.3 s each.

### Google Translate (the headline experiment)

```bash
python scripts/run_back_translation.py --translator google
python scripts/run_telephone_chain.py   --translator google
python scripts/run_round_trip.py        --translator google
python scripts/make_figures.py
```

### NLLB-200 (the comparison experiment)

NLLB-200 is a research model from Meta, run **locally** — no rate limits, but
needs ~3 GB of disk and either a GPU or patience.

```bash
pip install -e .[nllb]
python scripts/run_back_translation.py --translator nllb
```

See [`docs/nllb_setup.md`](docs/nllb_setup.md) for hardware notes and what to
expect on CPU vs. GPU vs. Apple Silicon.

## What's in `data/`

| Path | Format | Description |
|---|---|---|
| `corpora/{domain}.txt` | text | Source sentences, one per line, 6 domains × ~100 sentences each. |
| `results/google/back_translation_long.csv` | long | One row per (translator × language × domain), 270 rows total. **Use this for plotting and analysis.** |
| `results/google/back_translation_wide.csv` | wide | One row per (translator × language), all (domain × metric) cells as columns. Convenient for spreadsheets. |
| `results/google/per_family/{family}.csv` | wide | Per-family checkpoints written incrementally during the run. |
| `translation_cache.json.gz` | gzipped JSON | MD5-keyed cache of every translation made; read by `experiments` modules transparently. |

Field-level documentation lives in [`data/README.md`](data/README.md).

## Methodology summary

* **Corpora.** Six register-distinct domains, each ~100 sentences:
  conversational, cultural, idiomatic, technical, legal, emotional. All
  English-source. See [`data/corpora`](data/corpora/) and
  [`docs/methodology.md`](docs/methodology.md) for the corpus design.
* **Languages.** 45 target languages distributed across 8 typological families
  (Romance 7, Germanic 7, Slavic 9, Semitic 3, East Asian 3, South & SE Asian
  9, Turkic 4, Uralic 3). Selection criteria: Google Translate coverage,
  family representativeness, script diversity.
* **Metrics.** Two surface-form metrics (BLEU and TER, via `sacrebleu`) and
  two semantic metrics (spaCy `en_core_web_md` cosine similarity on word
  vectors, and sentence-transformer cosine on `all-MiniLM-L6-v2` embeddings).
* **Statistics.** One-way ANOVA on each factor, η²-style variance
  decomposition, Pearson correlations between metrics.

## Limitations

* Single source language (English) — cross-source-language comparison is a
  natural extension.
* The free Google Translate endpoint changes silently, so absolute scores
  are time-stamped to the run date, not stable. The NLLB checkpoint is
  fixed and reproducible.
* Domain corpora are author-curated (one writer); a multi-author corpus
  would tighten the within-domain noise.

## License

MIT — see [LICENSE](LICENSE).

## Citation

If you use this code or data, please cite:

```bibtex
@misc{jack2026fidelity,
  title  = {Translation Fidelity Atlas: A multi-family,
            multi-domain back-translation benchmark},
  author = {Jackson, Daniel},
  year   = {2026},
  url    = {https://github.com/danjack0/translation-fidelity-atlas}
}
```
