# Findings (Google Translate run)

This document writes up what falls out of the single-pivot back-translation
results. The NLLB-200 comparison run is in progress; this page will be
updated when those results land.

All numbers come from
[`data/results/google/back_translation_long.csv`](../data/results/google/back_translation_long.csv).
The full analysis can be reproduced with `python scripts/analyse.py`.

## 1. Family dominates domain (on BLEU)

A one-way ANOVA on each factor gives:

| Factor | F | p | η² |
|---|---|---|---|
| Family | 42.44 (df 7, 262) | < 0.001 | **0.531** |
| Domain | 10.02 (df 5, 264) | < 0.001 | **0.160** |

By BLEU, language family explains **3.3× more variance than content domain**.
Both effects are highly significant, but the magnitudes are very different.
This is the headline result.

The picture changes when we switch to cosine similarity:

| Factor | F | p | η² |
|---|---|---|---|
| Family | 21.97 | < 0.001 | **0.370** |
| Domain | 22.58 | < 0.001 | **0.300** |

On cosine similarity, family and domain contribute roughly equally. Form
preservation (BLEU) is dominated by family; meaning preservation (cosine)
distributes between the two factors.

## 2. Family ranking

Sorted by mean BLEU across all (language × domain) cells:

| Family | Mean BLEU | SD | Mean Cosine | n cells |
|---|---:|---:|---:|---:|
| Germanic         | 74.36 | 7.52 | 0.9899 | 42 |
| Semitic          | 73.07 | 6.83 | 0.9891 | 18 |
| Romance          | 71.22 | 6.05 | 0.9876 | 42 |
| Slavic           | 63.42 | 5.81 | 0.9847 | 54 |
| South & SE Asian | 61.61 | 7.64 | 0.9825 | 54 |
| Uralic           | 61.38 | 5.80 | 0.9817 | 18 |
| Turkic           | 55.66 | 6.27 | 0.9794 | 24 |
| East Asian       | 50.99 | 5.84 | 0.9782 | 18 |

The Germanic ↔ East Asian gap is **23.4 BLEU points**, larger than the worst
domain effect within any one family. The ranking aligns broadly with
typological distance from English: Indo-European Western families top the
list; non-Indo-European or distantly related families bottom it. The
exception is Semitic, which lands second despite being non-Indo-European —
likely a function of high-resource pivots (Arabic, Hebrew) and well-trained
Google Translate models.

## 3. Domain ranking flips between metrics

This is the most interesting result. Sorted by **BLEU**:

| Domain | Mean BLEU | Mean Cosine |
|---|---:|---:|
| Technical       | 72.71 | 0.9842 |
| Conversational  | 64.49 | 0.9886 |
| Idiomatic       | 64.37 | 0.9809 |
| Legal           | 64.21 | 0.9857 |
| Cultural        | 64.05 | 0.9801 |
| Emotional       | 59.92 | 0.9887 |

By BLEU, technical text is the easiest to round-trip (72.7) and emotional
text is the hardest (59.9) — a 13-point gap.

Sorted by **cosine similarity**:

| Domain | Mean Cosine | Mean BLEU |
|---|---:|---:|
| Emotional       | 0.9887 | 59.92 |
| Conversational  | 0.9886 | 64.49 |
| Legal           | 0.9857 | 64.21 |
| Technical       | 0.9842 | 72.71 |
| Idiomatic       | 0.9809 | 64.37 |
| Cultural        | 0.9801 | 64.05 |

Now emotional text is *most* preserved and technical drops to fourth.
Idiomatic and cultural are at the bottom of both rankings — the only
domains that fail in form *and* meaning.

The story: technical terminology and named entities survive intact word-
for-word (high BLEU), but their *meaning* is preserved no better than
emotional content's meaning is. Emotional and conversational text has the
opposite shape — surface form drifts (lower BLEU) but the underlying
meaning rides through (high cosine). This is exactly the form-vs-meaning
distinction that motivates having both metric families: if we used only
BLEU we would conclude that emotional translation is the hard problem and
technical is solved; in cosine similarity terms, that's not what's
happening.

## 4. Metric correlations

Pairwise Pearson correlations across the 270 cells:

|  | Cosine | BLEU | TER | Embedding |
|---|---:|---:|---:|---:|
| Cosine    | 1.000 | 0.651 | -0.627 | 0.371 |
| BLEU      | 0.651 | 1.000 | -0.972 | 0.664 |
| TER       | -0.627 | -0.972 | 1.000 | -0.561 |
| Embedding | 0.371 | 0.664 | -0.561 | 1.000 |

All correlations significant at *p* < 0.001 (n = 270).

Three observations:

1. **BLEU and TER are almost perfectly anti-correlated** (r = −0.972).
   They essentially measure the same surface-form signal from opposite
   directions. Reporting both is informative for direction-of-error
   reasoning but adds little independent variance.
2. **Cosine and embedding are only weakly correlated** (r = 0.371). They
   are both "semantic" metrics in the sense that they compare embeddings,
   but spaCy's word-vector averages and sentence-transformer encodings
   capture meaning differently. Word-vector averages are dominated by
   lexical overlap; sentence transformers compress more of the
   compositional meaning. Treating them as interchangeable would be wrong.
3. **Cosine ↔ BLEU correlate moderately** (r = 0.651). This is the gap
   that produces the form-vs-meaning story above: the metrics agree on
   broad strokes (which families are easier) but disagree on details
   (which domains are easier).

## 5. Extreme cells

**Highest-fidelity cells (top 5 by BLEU):**

| Family | Language | Domain | BLEU |
|---|---|---|---:|
| Germanic | Danish (`da`)     | Technical | 86.78 |
| Germanic | Norwegian (`no`)  | Technical | 86.26 |
| Germanic | Swedish (`sv`)    | Technical | 85.90 |
| Germanic | Afrikaans (`af`)  | Technical | 84.97 |
| Germanic | Afrikaans (`af`)  | Legal     | 84.46 |

**Lowest-fidelity cells (bottom 5 by BLEU):**

| Family | Language | Domain | BLEU |
|---|---|---|---:|
| South & SE Asian | Thai (`th`)        | Legal          | 39.99 |
| East Asian       | Chinese (`zh-CN`)  | Idiomatic      | 42.05 |
| South & SE Asian | Thai (`th`)        | Emotional      | 43.91 |
| East Asian       | Korean (`ko`)      | Conversational | 44.71 |
| Turkic           | Kazakh (`kk`)      | Emotional      | 44.88 |

The Germanic-technical sweep at the top is striking — five of the top six
cells are Germanic technical or legal. The bottom is more diverse: failure
spreads across families and domains. It is harder to be reliably good at
back-translation than reliably bad.

## 6. What's missing (work in progress)

* **NLLB-200 comparison run.** Code is implemented, will be run once the
  600M-distilled checkpoint can be staged on appropriate hardware. The
  research interest is whether NLLB closes the East-Asian gap (it was
  trained with explicit attention to lower-resource families) and whether
  the form-vs-meaning split changes shape on a non-commercial system.
* **Telephone-chain results.** Three orderings × six domains, code complete,
  not yet run.
* **ABA / BAB directional asymmetry.** Code complete, not yet run.

## 7. Interpretation cautions

* "Family" here is a typological label, not a model-internal feature.
  Google Translate does not "know" what family a language belongs to;
  family is an analyst-imposed grouping. The result that family explains
  more variance than domain is a *post hoc* observation about data
  resource and architectural choices made during model training.
* Free Google Translate is a moving target. These results are time-stamped
  to the run that produced
  [`back_translation_long.csv`](../data/results/google/back_translation_long.csv).
  Re-running might yield different absolute scores; rankings should be
  more stable.
* All sentences are author-curated. A multi-author corpus would tighten the
  within-domain variance and let us decompose corpus-author effects from
  domain effects.
