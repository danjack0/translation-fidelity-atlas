# Methodology

## Research question

When a sentence is translated to a foreign language and back to its source,
how much of the original is preserved — and what predicts that preservation?
Specifically, does the typological distance of the pivot language matter
more than the linguistic register of the source text, or vice versa?

The classical "back-translation" approach to MT evaluation has been criticized
for confusing two error sources: errors made on the way out, and errors made
on the way back. We work around that by combining three complementary
protocols, two metric families, and two MT systems.

## Corpora

Six English-source corpora, each curated to be register-distinct and roughly
~100 sentences:

| Domain | Description | Examples |
|---|---|---|
| **Conversational** | Everyday speech, contractions, casual register. | "I'm not gonna lie, that caught me off guard." |
| **Cultural** | Practices and references rooted in a specific culture (US-centric here). | "He filed his taxes by the April deadline." |
| **Emotional** | Affect-heavy first-person prose; trauma, grief, relief. | "My hands wouldn't stop shaking as I waited for the judge." |
| **Idiomatic** | Figurative language whose surface form does not match its meaning. | "She let the cat out of the bag." |
| **Technical** | Software / systems / engineering register, dense in named entities. | "The deployment pipeline includes automated unit and integration testing." |
| **Legal** | Procedural and contractual register, dense in fixed-form Latinate phrases. | "The court applied settled case law to determine the statute had not been tolled." |

Domain selection follows the standard linguistics distinction between
**register** (style/formality) and **field** (subject matter). The six
domains span both axes: technical and legal are formal and field-specific;
conversational and emotional are informal and register-specific; cultural
and idiomatic are mixed.

## Languages

45 target languages spanning 8 typological families:

| Family | Languages | n |
|---|---|---|
| Romance        | it, es, fr, pt, ro, ca, gl                   | 7 |
| Germanic       | de, nl, sv, da, no, af, is                   | 7 |
| Slavic         | ru, pl, cs, uk, bg, sr, hr, sk, sl           | 9 |
| Semitic        | ar, iw, mt                                    | 3 |
| East Asian     | zh-CN, ja, ko                                | 3 |
| South & SE Asian | hi, bn, ur, ta, te, th, vi, id, ms         | 9 |
| Turkic         | tr, az, kk, uz                               | 4 |
| Uralic         | fi, et, hu                                   | 3 |

Selection criteria: complete Google Translate coverage, multiple
representatives per family where available, and script diversity (Latin,
Cyrillic, Arabic, CJK, Indic).

## Translation systems

Two systems are compared:

* **Google Translate** — closed commercial system, accessed via
  `deep_translator`'s scraping wrapper. Continuously updated; results are
  timestamped to the run date.
* **NLLB-200** ("No Language Left Behind", Meta AI 2022) — open research
  model, run locally via Hugging Face `transformers`. Default checkpoint is
  the 600M-parameter distilled variant; the 1.3B variant is also supported.

The two were chosen specifically for contrast: a black-box production system
versus a research baseline with a fixed checkpoint, known training data, and
known architecture. Differences between them are interpretable — Google
diverging from NLLB on a given language pair is informative in a way that
"two commercial APIs disagree" is not.

## Experiments

### Single-pivot back-translation

For every (system × family × language × domain) cell:

1. Translate `en` → target language.
2. Translate target language → `en`.
3. Score the back-translated English against the original.

This yields 2 systems × 45 languages × 6 domains = 540 cells per run, each
scored on four metrics (cosine, BLEU, TER, embedding).

### Telephone chain (multi-hop)

Translate through a chain of intermediate languages, scoring at each hop by
detouring back to English purely for evaluation (the chain itself remains in
non-English). Three orderings are run for every system:

* **Linguistic** — increasing typological distance from English:
  `es → de → ru → ar → ja`.
* **Reverse** — the linguistic chain reversed.
* **Random** — a fixed random shuffle (`ru, es, ja, de, ar`), seed-frozen for
  reproducibility.

The chain experiment isolates *compounding* error from single-pivot error:
each hop's degradation is layered on top of every previous one. Comparing
the three orderings tests whether the order matters or only the set of
languages used.

### Round-trip directional asymmetry (ABA / BAB)

For each language and domain:

* **ABA** (English-anchored): `en → tgt → en`, scored against the original
  English.
* **BAB** (target-anchored): `tgt → en → tgt`, scored against the
  first-pass `en → tgt` output.

If a system were perfectly symmetric on a language pair, ABA and BAB
fidelity would be equal. Any divergence reveals a *directional asymmetry* —
the system handles one translation direction better than the other.

## Metrics

Four fidelity metrics in two families:

### Surface-form (lexical)
* **BLEU** — corpus-level, via `sacrebleu`. Range 0–100, higher better.
* **TER** (Translation Edit Rate) — corpus-level, via `sacrebleu`. Range 0+,
  **lower better**.

### Semantic
* **Cosine similarity** on spaCy's `en_core_web_md` word-vector averages.
  Range 0–1, higher better.
* **Embedding similarity** — sentence-transformer cosine on
  `all-MiniLM-L6-v2`. Range 0–1, higher better.

The two families are kept separate because they answer different questions:
"is the surface form preserved?" vs. "is the meaning preserved?". As the
results show, those questions can have different answers.

## Statistical analysis

* **Variance decomposition** (η²-style): for each metric, what fraction of
  the total sum of squares is attributable to family vs. domain?
* **One-way ANOVA**: does the metric differ across families? Across domains?
  Reported with F, p, and effect size (η²).
* **Pearson correlation matrices**: pairwise between metrics, per system.

All statistics are computed in
[`src/translation_fidelity_atlas/analysis/statistics.py`](../src/translation_fidelity_atlas/analysis/statistics.py)
and accessible via `python scripts/analyse.py`.

## Reproducibility

* Every translation is MD5-keyed by `(translator, src, tgt, text)` and
  cached on disk. Re-running an experiment after adding a new domain or
  language only hits the API for the new cells.
* The committed cache (`data/translation_cache.json.gz`, 3 MB gzipped, 54k
  entries) covers the full Google Translate single-pivot run.
* All random orderings are seed-frozen.
* Library versions are pinned in `pyproject.toml`.
