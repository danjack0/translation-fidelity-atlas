# Findings — the Google Translate run

A deep dive on **one of the two systems** in this benchmark. Everything on this
page is computed from the Google Translate single-pivot back-translation run
only:
[`data/results/google/back_translation_long.csv`](../data/results/google/back_translation_long.csv),
270 cells. Reproduce with `python scripts/analyse.py --metric bleu`.

This page is deliberately **not** a two-system analysis. The cross-system
comparison — what replicates between Google Translate and NLLB-200 and what does
not — lives in the top-level README's
[Typology travels. Domain difficulty belongs to the system.](../README.md#typology-travels-domain-difficulty-belongs-to-the-system)
section, with the full derivation in
[`VERIFIED_FACTS.md §7`](../VERIFIED_FACTS.md#7-do-google-and-nllb-agree-on-the-headline-findings).
Keeping the cross-system findings in one place avoids two documents that have to
be kept in sync.

> ### ⚠ Scope: which of these findings survive a change of system
>
> Both systems ran at full parity (identical 45 languages, 8 families, 6 domains,
> all three protocols), so every claim here has been checked against NLLB-200.
> The answer splits cleanly:
>
> * **The family-level findings replicate.** Family still dominates domain on
>   BLEU under NLLB (η² 0.52 vs 0.18), and the family *ranking* transfers almost
>   intact — Spearman **ρ = +0.90** (*p* = 0.002). East Asian is worst under both.
>   §1 and §2 below are therefore about *language*, not about Google.
> * **The domain-level findings do not.** The domain ranking is uncorrelated
>   across the two systems — Spearman **ρ = +0.09** (*p* = 0.87). Technical goes
>   from **1st under Google to 5th of 6 under NLLB**; emotional goes from
>   **worst (6th) to 3rd best**. So §3 — and every domain claim anywhere on this
>   page — describes *Google Translate*, not back-translation in general.
>
> Details: [`VERIFIED_FACTS.md §7c`](../VERIFIED_FACTS.md#7c-where-they-disagree--the-domain-finding-does-not-replicate).

## 1. Family dominates domain (on BLEU)

A one-way ANOVA on each factor gives:

| Factor | F | p | η² |
|---|---|---|---|
| Family | 42.44 (df 7, 262) | < 0.001 | **0.531** |
| Domain | 10.02 (df 5, 264) | < 0.001 | **0.160** |

By BLEU, language family explains **3.3× more variance than content domain**.
Both effects are highly significant, but the magnitudes are very different.
This is the headline result — and it is the one that **replicates under
NLLB-200** (η² 0.52 vs 0.18, a 2.88× ratio).

The picture changes when we switch to cosine similarity:

| Factor | F | p | η² |
|---|---|---|---|
| Family | 21.97 | < 0.001 | **0.370** |
| Domain | 22.58 | < 0.001 | **0.300** |

On cosine similarity, family and domain contribute roughly equally. Form
preservation (BLEU) is dominated by family; meaning preservation (cosine)
distributes between the two factors.

A scope note on "family dominates": that is a **surface-form** result. It holds
on BLEU and TER for both systems, but inverts on one semantic metric in each —
under Google's sentence-transformer embedding, domain wins (η² 0.557 vs family
0.192). "Family explains more variance" is true of how much the *wording*
changes, not of how much the *meaning* changes
([`§6`](../VERIFIED_FACTS.md#6-recomputed-statistics-per-backend)).

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

**This ordering transfers.** Under NLLB-200 the same ranking comes back at
Spearman ρ = +0.90: East Asian worst in both, Turkic second-worst in both,
Germanic and Romance the top two in both. Semitic slips from 2nd to 3rd, which
is consistent with the high-resource explanation above being Google-specific
while the broad typological gradient is not.

## 3. Domain ranking flips between metrics *(Google-specific)*

> **This section does not replicate under NLLB-200** (domain rank ρ = +0.09,
> *p* = 0.87). Read every number below as a fact about Google Translate.

Sorted by **BLEU**:

| Domain | Mean BLEU | Mean Cosine |
|---|---:|---:|
| Technical       | 72.71 | 0.9842 |
| Conversational  | 64.49 | 0.9886 |
| Idiomatic       | 64.37 | 0.9809 |
| Legal           | 64.21 | 0.9857 |
| Cultural        | 64.05 | 0.9801 |
| Emotional       | 59.92 | 0.9887 |

By BLEU, technical text is the easiest to round-trip (72.7) and emotional
text is the hardest (59.9) — a 13-point gap. Note how narrow the middle is:
four domains sit inside a 0.5-point band (64.05–64.49), so the only real
separations here are technical above and emotional below.

Sorted by **cosine similarity**:

| Domain | Mean Cosine | Mean BLEU |
|---|---:|---:|
| Emotional       | 0.9887 | 59.92 |
| Conversational  | 0.9886 | 64.49 |
| Legal           | 0.9857 | 64.21 |
| Technical       | 0.9842 | 72.71 |
| Idiomatic       | 0.9809 | 64.37 |
| Cultural        | 0.9801 | 64.05 |

Now emotional text is *most* preserved and technical drops to fourth. The
cleanest illustration of the split is **emotional**, which is simultaneously the
**worst** domain on BLEU (59.92) and the **best** on cosine (0.9887) — the words
come back different, the meaning comes back intact. Cultural is the mirror case,
last on cosine and fifth on BLEU. Idiomatic is *not* a both-metrics failure: it
is second-worst on cosine (0.9809) but **third-best on BLEU** (64.37), above
legal and cultural
([`§7d`](../VERIFIED_FACTS.md#7d-a-readme-claim-that-is-wrong-for-both-backends)).

The story: technical terminology and named entities survive intact word-
for-word (high BLEU), but their *meaning* is preserved no better than
emotional content's meaning is. Emotional and conversational text has the
opposite shape — surface form drifts (lower BLEU) but the underlying
meaning rides through (high cosine). This is exactly the form-vs-meaning
distinction that motivates having both metric families: if we used only
BLEU we would conclude that emotional translation is the hard problem and
technical is solved; in cosine similarity terms, that's not what's
happening.

That form/meaning gap is itself real in both systems, though **about half as
large under NLLB** (Pearson *r* between BLEU and cosine is 0.651 for Google
against 0.761 for NLLB). What does *not* carry over is which specific domains
land where.

## 4. Metric correlations

Pairwise Pearson correlations across the 270 cells:

|  | Cosine | BLEU | TER | Embedding |
|---|---:|---:|---:|---:|
| Cosine    | 1.000 | 0.651 | -0.627 | 0.371 |
| BLEU      | 0.651 | 1.000 | -0.972 | 0.664 |
| TER       | -0.627 | -0.972 | 1.000 | -0.766 |
| Embedding | 0.371 | 0.664 | -0.766 | 1.000 |

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
cells are Germanic technical or legal (the sixth is Galician technical, 83.77).
The bottom is more diverse: failure spreads across families and domains. It is
harder to be reliably good at back-translation than reliably bad.

Under NLLB-200 the extremes are different in both level and identity: the best
cell is Norwegian conversational at 63.97 and the worst is Croatian legal at
7.19, the latter flagged as a possible data-quality issue rather than a
diagnosed result.

## 6. What this page does not cover

Nothing listed here is blocked or unrun — the data exists and is committed. This
is a scope boundary, not a backlog.

* **The other system.** NLLB-200 ran at full parity and its results are in
  [`data/results/nllb/`](../data/results/nllb/). Its per-backend figures are in
  [`figures/`](../figures/). The cross-system analysis is in the README and
  `VERIFIED_FACTS.md §7`, not here.
* **The other two protocols.** This page writes up **single-pivot
  back-translation only**. The telephone-chain (108 rows per backend) and
  ABA/BAB round-trip (60 rows per backend) results are committed for both
  systems and plotted in `figures/`, but have no prose write-up yet. That is the
  clearest piece of genuine remaining work.
* **The Croatian legal outlier.** NLLB scores `hr` legal at BLEU 7.19, roughly
  28 points below the mean of its own domain and an 8.65× drop from Google's
  62.21 on the same cell. Whether that is a real result or a data-quality
  problem is undiagnosed.

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
* **Do not generalise the domain results.** They are the part of this page that
  demonstrably fails to survive a change of translation system. Any domain-level
  claim taken from here needs "under Google Translate" attached to it.
