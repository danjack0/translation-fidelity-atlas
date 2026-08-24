# VERIFIED_FACTS.md

Audit of `README.md` against the committed code and data, at
`7d20fa2` (`Merge remote-tracking branch 'origin/snapshot/desktop'`) — the
first commit where the NLLB results are on `main`.

**Method.** Every number below is derived from artifacts (CSVs, the gzipped
cache, `config.py`, `git`), never from README prose. No API calls, no
retraining, no re-running of experiments. Figures were **not** regenerated —
committed PNGs were inspected as-is.

Two throwaway helper scripts were written for this audit and are referenced
below as source commands: `_audit_cache.py` (deterministic cache-key replay)
and `_audit_stats.py` (statistics recomputation). Both are read-only and
untracked. Nothing was committed.

Legend: **OK** = README matches artifacts · **WRONG** = contradicted by
artifacts · **STALE** = was true pre-NLLB, false now · **INCOMPLETE** =
true but materially omits something · **UNVERIFIED** = cannot be checked
read-only.

> **Reading this document after the fact.** Findings are preserved as written at
> `7d20fa2`, each annotated with a **RESOLVED / FIXED** note where the repo has
> since changed. Two consequences for the reader:
>
> * **Every `line NN` reference points at the README as it stood at `7d20fa2`.**
>   That README has since been rewritten from a Google-only project page into a
>   two-system study, so the ~21 line numbers cited below **will not match** the
>   current file. They are historical coordinates, not navigation.
> * The helper scripts cited as `_audit_cache.py` / `_audit_stats.py` were
>   untracked at audit time. Equivalents are now committed as
>   `scripts/audit_cache.py` and `scripts/audit_stats.py`.
> * The **Method** note above ("Figures were not regenerated") describes the
>   audit itself and remains true of it. The figures **have** since been
>   regenerated in the course of resolving §8; no statistic in this document was
>   recomputed as a result, and none changed.
>
> **Current standing: every finding in this audit is resolved except two lines
> of package metadata in `pyproject.toml` (§9), plus items that were always
> UNVERIFIED by nature (Appendix C).**

---

## Executive summary

| # | Area | Verdict |
|---|---|---|
| 1 | Cache size (`54,025` / `54k` / `3 MB`) | **WRONG** — 141,088 entries, 8.09 MB. **→ FIXED** in README, `data/README.md` and `docs/methodology.md` |
| 2 | Row counts / 270 cells | **OK** |
| 3 | NLLB coverage = 45/8/6 | **OK** — full parity, not a subset |
| 4 | Chain + round-trip scope | **OK**, but README **INCOMPLETE** — Google *and* NLLB ran all three protocols; README documented only `results/google/`. **→ FIXED**: README now documents both backends and all three protocols |
| 5 | "141,088 translations" | **Defensible with wording care** — it is exactly `len(cache)`; it is *not* the number of translation operations (162,000). No API counter exists in the code. **→ APPLIED**: all three docs now say "unique cached translations" and give 162,000 separately |
| 6 | Google headline statistics | **OK** — all 9 TL;DR numbers reproduce |
| 7 | Google vs NLLB agreement | **Family finding holds. Domain finding REVERSES.** See §7 |
| 8 | Figures | *At audit:* 43 PNGs; **STALE/INCOMPLETE** — chain and round-trip figures Google-only despite NLLB data existing. **→ FULLY RESOLVED:** 52 PNGs, 21/21 per-backend parity, scatter split per system, `figures/README.md` rebuilt. See §8 |
| 9 | Clone URL vs BibTeX URL | **WRONG — mismatched** `danjackdev` vs `danjack0`. **→ FIXED in README** (both now `danjack0`). **STILL OPEN elsewhere:** `pyproject.toml:57` keeps the `danjackdev` URL, and `pyproject.toml:12` names the author "Daniel Jack" against "Daniel Jackson" in LICENSE and BibTeX. See §9 |

The single most consequential finding is **§7**: the README's form-versus-meaning
narrative — which it calls "the most interesting result" — is a Google-only
result, and its central BLEU claim **reverses sign** under NLLB.

---

## 1. Unique keys in `data/translation_cache.json.gz`

| Claim (README) | Verified value | Verdict |
|---|---|---|
| "54k cached translations (3 MB gzipped)" (line 52) | **141,088 entries, 8,093,383 bytes (7.72 MiB / 8.09 MB)** | **WRONG** |
| "holds 54,025 translations from the Google run" (line 85) | Google-attributable share is **69,962**, not 54,025 | **WRONG** |

```bash
python -c "import gzip,json,os; c=json.load(gzip.open('data/translation_cache.json.gz','rt',encoding='utf-8')); print(len(c),'keys'); print(os.path.getsize('data/translation_cache.json.gz'),'bytes')"
# 141088 keys
# 8093383 bytes
```

### Do keys encode the backend?

**No — not readably.** All 141,088 keys are 32-char MD5 hex digests of
`f"{translator}|{src}|{tgt}|{text}"` (`src/translation_fidelity_atlas/translators/cache.py:27-30`).
The backend is *inside* the hash preimage, so it cannot be read off a key.

```bash
python -c "import gzip,json; c=json.load(gzip.open('data/translation_cache.json.gz','rt',encoding='utf-8')); print('all 32-char hex:', all(len(k)==32 and all(ch in '0123456789abcdef' for ch in k) for k in c))"
# all 32-char hex: True
```

### Backend breakdown (recovered by deterministic replay)

The split *is* recoverable without any API call: forward keys are computable
from the committed corpora, and each forward value supplies the input text for
the next hop's key. Replaying all three protocols for both backends attributes
**141,049 of 141,088** keys, with **zero cache misses**.

| Backend | Unique keys | Share |
|---|---|---|
| `google` | **69,923** (+39 stray, see below) = **69,962** | 49.6% |
| `nllb` | **71,126** | 50.4% |
| overlap | **0** (translator name is inside the hash) | — |
| **total** | **141,088** | 100% |

```bash
python _audit_cache.py
# attributed: 141049  unattributed: 39
# google 69923 / nllb 71126 / overlap 0
# -- lookups that MISSED the cache --   (none)
```

Cross-check against history — the initial (Google-only) commit's cache is
exactly the Google share, and the NLLB merge added exactly the NLLB share:

```bash
git show 2d8b6a4:data/translation_cache.json.gz > ./_cache_initial.json.gz
python -c "import gzip,json; i=json.load(gzip.open('./_cache_initial.json.gz','rt',encoding='utf-8')); c=json.load(gzip.open('data/translation_cache.json.gz','rt',encoding='utf-8')); print(len(i),len(c),len(set(c)-set(i)), set(i)<=set(c), sum(c[k]!=i[k] for k in i))"
# 69962 141088 71126 True 0
```
→ initial commit **69,962** keys · HEAD **141,088** · NLLB merge added
**71,126** · every pre-existing key retained, **0** values changed.

**The 39 unattributed keys** are all `google`, all present since the initial
commit, and all pass-through/failure-path entries (input ≈ output — the
`return text  # preserve corpus alignment` branch at
`experiments/back_translation.py:66`), mostly `ru→en`, `pl→en`, `cs→en`,
`uk→en`. All 39 were identified by brute-force preimage search; none is an
unexplained artifact. They are cache entries but arguably **not successful
translations**.

> **Note on `54,025`.** Google's *back-translation protocol alone* accounts for
> exactly **54,000** keys. `54,025` is therefore plausibly a back-translation-only
> count from a run predating the committed cache — but it does not match the
> committed file at *any* commit in this repo's history. Origin of the exact
> figure `54,025`: **UNVERIFIED**.

Same stale number also appears in `data/README.md:93` ("Entries: 54,025 (Google
run only)", "~3.1 MB gzipped") and `docs/methodology.md:150` ("3 MB gzipped, 54k
entries"). Both **WRONG** by the same measurement.

> **RESOLVED — all three files corrected.** `README.md`, `data/README.md` and
> `docs/methodology.md` now each state **141,088 unique cached translations,
> 8.09 MB gzipped**, split 69,962 Google / 71,126 NLLB with zero overlap, and
> each words it as `len(cache)` rather than a count of operations, per §5. Two
> further errors were found and fixed while correcting `data/README.md`: it also
> claimed "~8.0 MB raw" (the uncompressed size is **~20.5 MB**) and listed the
> corpora at 99 sentences each (**100** each, 600 total — `wc -l` undercounts
> because there is no trailing newline).

---

## 2. Row counts and scored cells

```bash
python -c "
import pandas as pd
for f in ['data/results/google/back_translation_long.csv','data/results/nllb/back_translation_long.csv','data/results/combined_long.csv']:
    print(f, len(pd.read_csv(f)))"
```

| File | Claim | Verified | Verdict |
|---|---|---|---|
| `google/back_translation_long.csv` | "270 rows total" (line 117) | **270** | **OK** |
| `nllb/back_translation_long.csv` | *(not mentioned)* | **270** | **INCOMPLETE** |
| `combined_long.csv` | *(not mentioned)* | **540** | **INCOMPLETE** |

> **RESOLVED.** Both files are now documented. The README's "What's in `data/`"
> table lists `results/nllb/` in full and `results/combined_long.csv` (540 rows),
> and `data/README.md` documents every file under both backends with verified
> row counts.

**Total scored (translator × language × domain) cells: 540.**
= 2 translators × 45 languages × 6 domains. Verified exactly: 45 × 6 = 270 per
backend, 0 duplicate cells, 0 NaNs in any metric column.

```bash
python -c "
import pandas as pd
for b in ['google','nllb']:
    d=pd.read_csv(f'data/results/{b}/back_translation_long.csv')
    print(b, len(d), d.duplicated(['translator','language','domain']).sum(), d.isna().sum().sum())"
# google 270 0 0
# nllb 270 0 0
```

`combined_long.csv` is a faithful concatenation (verified row-for-row, not
assumed):

```bash
python _audit_stats.py   # tail section
# combined == google+nllb concatenated: True
# combined rows=540  per-translator={'google': 270, 'nllb': 270}
```

Supporting files are internally consistent: `back_translation_wide.csv` = 45
rows for each backend, and the 8 `per_family/*.csv` checkpoints sum to 45 rows
for each backend.

---

## 3. Languages, families, domains — NLLB vs Google

**NLLB covers the identical 45 / 8 / 6. It is not a subset.**

```bash
python -c "
import pandas as pd
g=pd.read_csv('data/results/google/back_translation_long.csv')
n=pd.read_csv('data/results/nllb/back_translation_long.csv')
for t,d in [('google',g),('nllb',n)]: print(t, d.language.nunique(), d.family.nunique(), d.domain.nunique())
print('identical lang sets:', set(g.language)==set(n.language))"
# google 45 8 6
# nllb 45 8 6
# identical lang sets: True
```

| | Google | NLLB | Identical? |
|---|---|---|---|
| Distinct languages | 45 | 45 | **Yes** (set-equal, zero asymmetric difference) |
| Typological families | 8 | 8 | **Yes** |
| Domains | 6 | 6 | **Yes** |

Both also match `config.py:LANGUAGE_FAMILIES` exactly (45 codes), and the
README's per-family counts (line 130-133) are correct:

```bash
python -c "from translation_fidelity_atlas.config import LANGUAGE_FAMILIES as L; print({k:len(v) for k,v in L.items()}); print('total', sum(map(len,L.values())))"
# {'romance': 7, 'germanic': 7, 'slavic': 9, 'semitic': 3, 'east_asian': 3, 'south_se_asian': 9, 'turkic': 4, 'uralic': 3}
# total 45
```

Corpora claim "6 × ~100 sentences" — verified as **exactly 100 each, 600 total**
(note `wc -l` reports 99: no trailing newline):

```bash
python -c "
from pathlib import Path
t=0
for p in sorted(Path('data/corpora').glob('*.txt')):
    n=len([l for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]); t+=n; print(p.name,n)
print('TOTAL',t)"
# each 100 ... TOTAL 600
```

---

## 4. Telephone chain and round-trip — scope, and whether Google equivalents exist

**Google equivalents exist for both. Every protocol ran for both backends.**
No protocol is single-backend.

```bash
python -c "
import pandas as pd
for b in ['google','nllb']:
    c=pd.read_csv(f'data/results/{b}/telephone_chain.csv'); r=pd.read_csv(f'data/results/{b}/round_trip.csv')
    print(b,'chain',len(c),sorted(c.order.unique()),sorted(c.hop.unique()))
    print(b,'round_trip',len(r),sorted(r.language.unique()),sorted(r.direction.unique()))"
```

| File | Rows | Scope | Google equivalent? |
|---|---|---|---|
| `nllb/telephone_chain.csv` | **108** | 3 orders × 6 domains × 6 hops (0–5) | **Yes** — `google/telephone_chain.csv`, also **108** rows |
| `nllb/round_trip.csv` | **60** | 5 languages (`ar de es ja ru`) × 6 domains × 2 directions (ABA/BAB) | **Yes** — `google/round_trip.csv`, also **60** rows |

- Chain: 3 × 6 × 6 = 108 ✓. Hop 0 is a synthetic perfect baseline
  (BLEU 100 / cosine 1.0 / TER 0), written without a translation call
  (`experiments/telephone_chain.py:69-78`) — so only 5 hops are measured, matching
  the README's "five-hop telephone chains".
- Round-trip: 5 × 6 × 2 = 60 ✓. The 5 languages are `CHAIN_ORDER_LINGUISTIC`,
  the documented default of `scripts/run_round_trip.py:36`.

**README gap (INCOMPLETE, not wrong):** the "What's in `data/`" table (lines
114-121) and the repo-layout tree (line 51) list only `results/google/`. Eight
committed artifacts go undocumented: the 7 files under `data/results/nllb/` and
`data/results/combined_long.csv`. The README's "Reproducing the experiments"
section likewise shows all three protocols for Google (lines 92-97) but only
`run_back_translation.py` for NLLB (line 106) — understating what was actually
run, since `nllb/telephone_chain.csv` and `nllb/round_trip.csv` both exist.

> **RESOLVED.** The README's repo-layout tree and "What's in `data/`" table now
> show `results/google/` and `results/nllb/` side by side — including the
> `telephone_chain.csv` and `round_trip.csv` rows for both — plus
> `combined_long.csv`. "Reproducing the experiments" shows all three runners for
> both backends, noting each takes `--translator {google,nllb}`.

---

## 5. Total translations, and whether "141,088" is defensible

### Is there a running total logged anywhere in the code?

**No.** There is no API-call counter, no generation counter, no accumulator
anywhere in `src/` or `scripts/`.

```bash
grep -rn "n_calls\|api_calls\|call_count\|counter\|Counter()" --include=*.py src/ scripts/
# (no matches)
```

The **only** count ever logged is the cache's length:

```bash
grep -rn "log\.\(info\|debug\)" --include=*.py src/translation_fidelity_atlas/translators/cache.py
# cache.py:52: log.info("Loaded translation cache: %d entries from %s", len(cache), path)
# cache.py:75: log.debug("Cache saved (%d entries) → %s", len(cache), path)
```

`experiments/back_translation.py:188` logs only cell counts
(`"Done. %d (lang × domain) cells written."`), not translations.

### Where "141,088" came from

**It is exactly `len(cache)` at HEAD.** That is the only quantity in this
codebase that equals 141,088. Verdict: **defensible, but only with precise
wording.**

| Framing | Value | Defensible? |
|---|---|---|
| "141,088 **unique cached translations**" | 141,088 | **Yes** — exact, verified |
| "141,088 **translation operations / API calls**" | actual: **162,000** | **No** — understates by 20,912 |
| "141,088 **successful** translations" | 141,049 on-protocol; 39 are pass-through/failure-path | **No** — off by 39 |

### Total translations implied across ALL protocols and both backends

```bash
python _audit_cache.py    # lookups vs unique keys, per protocol
```

| Backend | Protocol | Lookups (operations) | Unique keys |
|---|---|---|---|
| google | back_translation | 54,000 | 54,000 |
| google | telephone_chain | 18,000 | 17,173 |
| google | round_trip | 9,000 | 8,637 |
| nllb | back_translation | 54,000 | 53,996 |
| nllb | telephone_chain | 18,000 | 17,884 |
| nllb | round_trip | 9,000 | 8,879 |
| | **TOTAL** | **162,000** | **141,049** (+39 stray = 141,088) |

Two distinct, both-correct numbers:

- **162,000 translation operations** implied by the protocols
  (81,000 per backend = 54,000 back-translation + 18,000 chain + 9,000 round-trip).
- **141,088 distinct translations stored**, because 20,951 operations are
  cache *hits* on work another protocol already did (e.g. round-trip's ABA leg
  re-uses back-translation's forward+back pass — verified 6,000 shared keys per
  backend; chain shares 3,887 with Google's other protocols, 3,633 for NLLB).

Derivation of 162,000 from first principles: 600 sentences × 45 languages × 2
directions = 54,000 back-translation; 600 × 3 orders × 5 hops × 2 (chain hop +
scoring detour to English) = 18,000 chain; 600 × 5 languages × 3 legs = 9,000
round-trip. Sum × 2 backends = 162,000.

**Reproducibility bonus (verified):** the replay recorded **zero** cache misses
across all six backend × protocol combinations. The committed cache fully covers
every protocol for both backends — re-running any experiment as committed costs
**0** API calls. This is *stronger* than the README's claim (line 85-88) that the
cache covers only the Google run. **(RESOLVED — the README, `data/README.md`
and `docs/methodology.md` now all state that the cache covers all three
protocols for both systems with zero replay misses.)** The "~0.3 s each" cache-miss cost is
**UNVERIFIED** (would require live API calls).

---

## 6. Recomputed statistics, per backend

```bash
python _audit_stats.py
```

`n = 270` cells per backend. ANOVA/η² via the repo's own
`analysis.one_way_anova`; correlations via `scipy.stats.pearsonr`.

### 6a. One-way ANOVA on BLEU — η² and p

| Factor | Google η² | Google F, p | NLLB η² | NLLB F, p |
|---|---|---|---|---|
| **family** | **0.5314** | F(7,262)=42.44, p=9.65e-40 | **0.5152** | F(7,262)=39.78, p=7.61e-38 |
| **domain** | **0.1596** | F(5,264)=10.02, p=8.49e-09 | **0.1789** | F(5,264)=11.50, p=4.65e-10 |
| family/domain ratio | **3.33×** | | **2.88×** | |

All four p-values are far below 0.001.

### 6b. η² across all four metrics — the "family dominates" claim is metric-dependent

| Metric | Google family | Google domain | NLLB family | NLLB domain |
|---|---|---|---|---|
| cosine | 0.3698 | 0.2996 | 0.1890 | **0.5206** ← domain wins |
| bleu | **0.5314** | 0.1596 | **0.5152** | 0.1789 |
| ter | **0.5357** | 0.1708 | **0.3791** | 0.0880 |
| embedding | 0.1919 | **0.5573** ← domain wins | **0.3706** | 0.2184 |

**Not in the README:** "family dominates domain" holds on the *surface-form*
metrics (BLEU, TER) for both backends, but **inverts on a semantic metric in
each backend** — Google embedding (domain 0.557 > family 0.192) and NLLB cosine
(domain 0.521 > family 0.189). The README's flat "Family (η² = 0.53) over domain
(η² = 0.16)" is true only of BLEU/TER.

### 6c. Pearson r — BLEU vs each cosine metric

| Pair | Google r (p) | NLLB r (p) |
|---|---|---|
| bleu ~ **cosine** (spaCy lexical) | **+0.6505** (7.12e-34) | **+0.7614** (2.24e-52) |
| bleu ~ **embedding** (MiniLM semantic) | **+0.6638** (1.15e-35) | **+0.6616** (2.29e-35) |
| cosine ~ embedding | +0.3714 (2.95e-10) | +0.3988 (9.93e-12) |
| bleu ~ ter *(reference)* | −0.9718 (4.40e-170) | −0.8985 (8.21e-98) |

README's `r = 0.651` (line 27) = Google `bleu~cosine` **0.6505** → **OK**, and
correctly scoped to the Google TL;DR table.

### 6d. Mean BLEU by family

| Family | Google | NLLB | Δ (nllb−google) |
|---|---|---|---|
| germanic | **74.36** (sd 7.52) | 50.66 (sd 9.42) | −23.69 |
| semitic | 73.07 (sd 6.83) | 46.07 (sd 8.04) | −27.00 |
| romance | 71.22 (sd 6.05) | **53.66** (sd 4.11) | −17.56 |
| slavic | 63.42 (sd 5.81) | 40.93 (sd 8.75) | −22.49 |
| south_se_asian | 61.61 (sd 7.64) | 41.09 (sd 7.90) | −20.51 |
| uralic | 61.38 (sd 5.80) | 34.48 (sd 7.05) | −26.89 |
| turkic | 55.66 (sd 6.27) | 30.24 (sd 7.09) | −25.42 |
| east_asian | **50.99** (sd 5.84) | **30.18** (sd 3.82) | −20.81 |

Best/worst gap: Google **23.37** (germanic − east_asian); NLLB **23.48**
(romance − east_asian).

### 6e. Mean BLEU by domain

| Domain | Google | NLLB | Δ |
|---|---|---|---|
| technical | **72.71** (best) | 39.04 (**5th of 6**) | −33.67 |
| conversational | 64.49 | **49.82** (best) | −14.67 |
| idiomatic | 64.37 | 44.81 | −19.56 |
| legal | 64.21 | **35.43** (worst) | −28.78 |
| cultural | 64.05 | 43.06 | −20.99 |
| emotional | **59.92** (worst) | 44.05 | −15.87 |

### 6f. Best / worst single cells (BLEU)

| | Google | NLLB |
|---|---|---|
| **Best** | `da` technical **86.78** | `no` conversational **63.97** |
| 2nd | `no` technical 86.26 | `no` idiomatic 63.60 |
| 3rd | `sv` technical 85.90 | `es` idiomatic 61.39 |
| **Worst** | `th` legal **39.99** | `hr` legal **7.19** |
| 2nd worst | `zh-CN` idiomatic 42.05 | `hr` technical 14.08 |
| 3rd worst | `th` emotional 43.91 | `th` legal 16.13 |

> `hr` (Croatian) legal at **BLEU 7.19** under NLLB is the lowest cell in
> either backend. Three comparisons, each against its correct referent:
>
> - **6.89 points** below NLLB's next-worst *cell* (`hr` technical, **14.08**).
> - **28.24 points** below NLLB's legal-*domain mean* (**35.43**) — this is
>   where the "28-point" figure comes from; it is a gap to a domain mean, not
>   to a neighbouring cell.
> - An **8.65× drop** from Google's own Croatian legal score (**62.21** → 7.19).
>
> The domain-mean gap is the one that makes the cell conspicuous: sitting 28
> points below the mean of its own domain is far more unusual than sitting 6.89
> points below the next cell up. Flagged as a possible data-quality issue worth
> a look; this audit does not diagnose it.

### 6g. README TL;DR spot-checks (Google) — all reproduce

| README claim (line) | Verified | Verdict |
|---|---|---|
| family η² = 0.53 (20) | 0.5314 | **OK** |
| domain η² = 0.16 (20) | 0.1596 | **OK** |
| 3.3× ratio (20) | 3.33× | **OK** |
| both p < 0.001 (20) | 9.65e-40 / 8.49e-09 | **OK** |
| Germanic best, 74.4 (21) | 74.36, rank 1 | **OK** |
| da/no/sv all > 85 technical (21) | 86.78 / 86.26 / 85.90 | **OK** |
| East Asian worst, 51.0 (22) | 50.99, rank 8 | **OK** |
| gap 23 BLEU (22) | 23.37 | **OK** |
| Technical best domain, 72.7 (23) | 72.71, rank 1 | **OK** |
| Emotional worst domain, 59.9 (24) | 59.92, rank 6 | **OK** |
| Thai legal 40.0, most degraded (25) | 39.99, is the minimum | **OK** |
| Danish technical 86.8, highest (26) | 86.78, is the maximum | **OK** |
| Pearson r = 0.651 (27) | 0.6505 | **OK** |

**All 13 Google headline numbers are accurate.** The TL;DR is correctly labelled
"(Google Translate)".

---

## 7. Do Google and NLLB agree on the headline findings?

*The most important question. Answer: they agree on family, and disagree
sharply on domain.*

```bash
python _audit_stats.py    # CROSS-BACKEND AGREEMENT section
```

### 7a. Does family still dominate domain for NLLB? — **YES**

| | Google | NLLB |
|---|---|---|
| family η² (BLEU) | 0.5314 | 0.5152 |
| domain η² (BLEU) | 0.1596 | 0.1789 |
| ratio | 3.33× | **2.88×** |
| both significant | p<1e-8 | p<1e-9 |

**CONFIRMED and replicated.** The magnitude is slightly attenuated (3.33× →
2.88×) but the finding is qualitatively identical and highly significant in both.

The family *ordering* also replicates strongly:

- Spearman ρ (family mean BLEU rank, Google vs NLLB) = **+0.9048** (p = 0.0020)
- `east_asian` is **worst in both**; `turkic` second-worst in both;
  `germanic`/`romance` are the top two in both (order swaps).
- Only material rank movement: `slavic` and `south_se_asian` swap (4th↔5th,
  0.16 BLEU apart in NLLB — noise), and `semitic` slips 2nd→3rd.

**This is a genuine cross-system replication and the README's strongest claim.**

### 7b. Is the BLEU-vs-cosine divergence present in both? — **YES, but weaker in NLLB**

| | Google | NLLB |
|---|---|---|
| Pearson r (bleu ~ cosine) | **0.651** | **0.761** |
| r² (shared variance) | 42% | 58% |

Divergence is present in both — neither is near r = 1, so form and meaning do
come apart under both systems. But NLLB's metrics are **substantially more
aligned** (r 0.761 vs 0.651; 58% vs 42% shared variance). The README's "**No.**
Pearson r = 0.651" is a Google-specific figure; the NLLB answer is a
weaker "no".

Corroborating: the domain rank-order disagreement between BLEU and cosine is
near-total for Google (Kendall τ = −0.067) but moderate and positive for NLLB
(τ = +0.467). **The form/meaning gap is real in both, but roughly half as large
in NLLB.**

### 7c. WHERE THEY DISAGREE — the domain finding does not replicate

**Spearman ρ (domain mean BLEU rank, Google vs NLLB) = +0.0857 (p = 0.8717).**
Statistically indistinguishable from zero. The domain ordering is essentially
uncorrelated across backends.

| Domain | Google rank | NLLB rank | Movement |
|---|---|---|---|
| technical | **1 (best, 72.71)** | **5 (39.04)** | ▼ 4 — **claim reverses** |
| legal | 4 (64.21) | **6 (worst, 35.43)** | ▼ 2 |
| conversational | 2 (64.49) | **1 (best, 49.82)** | ▲ 1 |
| emotional | **6 (worst, 59.92)** | 3 (44.05) | ▲ 3 — **claim reverses** |
| idiomatic | 3 (64.37) | 2 (44.81) | ▲ 1 |
| cultural | 5 (64.05) | 4 (43.06) | ▲ 1 |

Concretely, these README sentences are **Google-only and reverse under NLLB**:

- Line 23, "Best content domain? **Technical**" → under NLLB technical is 5th of
  6, and the domain README calls best (technical) suffers the **largest**
  backend penalty of any domain (−33.67 BLEU).
- Line 24, "Worst content domain? **Emotional**" → under NLLB emotional is 3rd
  **best**; legal is worst.
- Line 29-31, "By BLEU, technical text round-trips best; but by cosine … the
  most-preserved domains are emotional and conversational" → the **first half is
  false for NLLB**. The second half **does hold in both** (Google cosine top-2:
  emotional .9887, conversational .9886; NLLB cosine top-2: conversational .9830,
  emotional .9801) — **OK**.

These sit in the prose paragraph at lines 29-35, which — unlike the TL;DR
table — carries **no "(Google Translate)" qualifier**, so a reader will take it
as a project-level finding. It is not.

### 7d. A README claim that is wrong for *both* backends

Line 33-35: *"Idiomatic and cultural text are the worst on both metrics — they
fail in form *and* meaning, the only domains that do."*

**WRONG, even for Google.** On cosine the worst two *are* idiomatic (.9809) and
cultural (.9801) ✓ — but on BLEU, Google's worst domain is **emotional**
(59.92), and **idiomatic is 3rd-best** (64.37, above legal and cultural).
So idiomatic does not "fail in form" at all. Emotional is simultaneously
Google's **worst** BLEU domain and its **best** cosine domain — the exact
opposite of the stated pattern, and a cleaner illustration of the
form/meaning gap than the one the README chose.

Under NLLB the claim fails differently: worst-two BLEU are legal and technical;
worst-two cosine are technical and cultural.

> **RESOLVED — the claim is gone from both places it appeared.** The README's
> form/meaning section now uses emotional-under-Google (worst BLEU 59.92, best
> cosine 0.9887) as the illustration and states explicitly that idiomatic is
> second-worst on Google's cosine but **third-best on Google's BLEU**, so it does
> not fail in form. `docs/findings.md §3` carried the same false sentence
> ("Idiomatic and cultural are at the bottom of both rankings — the only domains
> that fail in form *and* meaning") and now carries the corrected version. A
> separate numeric error was found in that file while checking it: its metric
> correlation matrix gave TER ~ Embedding as **−0.561**; the recomputed value is
> **−0.766**, now fixed.

### 7e. Where the two backends do *not* disagree: absolute level

NLLB scores **uniformly lower** — every one of the 8 families and all 6 domains
drops. Mean BLEU 64.96 (Google) → 42.70 (NLLB), a −22.3 point shift; translator
identity alone accounts for η² = 0.546 of pooled BLEU variance
(F = 646.37, p = 3.02e-94). Cell-level agreement is moderate:

| Metric | Google~NLLB cell-level r | Spearman ρ | mean (G → N) |
|---|---|---|---|
| bleu | +0.5576 (1.83e-23) | +0.5559 | 64.96 → 42.70 |
| cosine | +0.6411 (1.17e-32) | +0.7019 | 0.98 → 0.97 |
| ter | +0.4844 (2.73e-17) | +0.5722 | 23.39 → 42.27 |
| embedding | +0.5998 (9.12e-28) | +0.5893 | 0.92 → 0.82 |

This is expected — `nllb-200-distilled-600M` is a 600M distilled research model
versus a production system — and the README's Limitations section (lines 143-146)
already anticipates that absolute scores aren't comparable. **Not a defect.** The
defect is that *relative domain ordering* also fails to replicate, which the
README does not anticipate.

### Bottom line for §7

| Finding | Replicates? |
|---|---|
| Family dominates domain on BLEU | **YES** — 3.33× vs 2.88×, ρ=+0.90 on family ranks |
| East Asian is the worst family | **YES** |
| BLEU and cosine diverge | **YES**, but ~half as strongly in NLLB (r .651 → .761) |
| Technical is the best domain | **NO — reverses** (1st → 5th) |
| Emotional is the worst domain | **NO — reverses** (6th → 3rd) |
| Domain ordering generally | **NO** — ρ=+0.086, p=0.87 |
| "Family dominates" on semantic metrics | **NO** — inverts for Google embedding and NLLB cosine |

---

## 8. Figures

> **Post-audit status: §8 is fully resolved.** The figure-coverage gap
> documented in this section has since been closed, the figures were
> regenerated, and `figures/README.md` was rebuilt. Every original finding is
> retained below as the state at `7d20fa2`, each followed by a **RESOLVED** note
> recording what was done. One arithmetic slip in the audit's own category table
> is corrected in §8a. The only item here still carrying a non-OK verdict is the
> "~30 seconds" runtime estimate, which remains **UNVERIFIED** because the
> regeneration was never timed — see Appendix C.

### 8a. Inventory

**At audit time:**

```bash
ls figures/*.png | wc -l          # 43
ls figures/ | grep -v '\.png$'    # README.md
```

**43 PNGs** (+ `figures/README.md`; 44 directory entries).

| Category | Count | Files |
|---|---|---|
| **Google-only** | **20** | 15 name-suffixed (`bar_family_{cosine,bleu,ter}_google`, `boxplot_{cosine,bleu,ter}_google`, `corr_matrix_google`, `radar_google`, `heatmap_google_{8 families}`) + `roundtrip_google` + **`asymmetry_heatmap`** + **`chain_degradation_{cosine,bleu,ter}`** |
| **NLLB-only** | **16** | `bar_family_{cosine,bleu,ter}_nllb`, `boxplot_{cosine,bleu,ter}_nllb`, `corr_matrix_nllb`, `radar_nllb`, `heatmap_nllb_{8 families}` |
| **Genuinely combined** | **7** | `bar_domain_{cosine,bleu,ter}` (grouped Google+Nllb bars), `scatter_{cosine_vs_bleu,cosine_vs_ter,bleu_vs_ter}` (pooled n=540) |

> **Correction to the table above (audit arithmetic, not a change in the
> artifacts).** The Google-only row enumerates **16** name-suffixed files
> (3 + 3 + 1 + 1 + 8), not 15, so Google-only was **21**, and "genuinely
> combined" was the 6 files listed, not 7. The two errors cancelled, which is
> why the total of 43 was still right. Verified against the tracked file list:
>
> ```bash
> git ls-files figures | grep -c '_google.*\.png'   # 17  (16 + roundtrip_google)
> git ls-files figures | grep -c '_nllb.*\.png'     # 16
> # unsuffixed: asymmetry_heatmap + chain_degradation×3 + bar_domain×3 + scatter×3 = 10
> # → 17 + 3 + 1 = 21 Google-only · 16 NLLB-only · 6 combined = 43
> ```

**RESOLVED — current inventory: 52 PNGs** (+ `figures/README.md`; 53 directory
entries). Per-backend coverage is now exactly symmetric, 21 / 21:

| Category | At audit | Now | What moved |
|---|---|---|---|
| **Google-only** | 21 | **21** | `asymmetry_heatmap` and `chain_degradation_{cosine,bleu,ter}` left this category (they became two-system); `asymmetry_heatmap_google` and `chain_degradation_{cosine,bleu,ter}_google` were added in their place |
| **NLLB-only** | 16 | **21** | **+5**: `roundtrip_nllb`, `chain_degradation_{cosine,bleu,ter}_nllb`, `asymmetry_heatmap_nllb` |
| **Genuinely two-system** | 6 | **10** | **+4**: `chain_degradation_{cosine,bleu,ter}` (now one row per system) and `asymmetry_heatmap` (now one column per system). The three `scatter_*` remain here but are now per-backend *panels* inside one file rather than a pooled cloud |
| **Total** | 43 | **52** | |

```bash
ls figures/*.png | wc -l          # 52
ls figures/ | grep -v '\.png$'    # README.md
```

### 8b. The coverage gap (at audit time)

The four unsuffixed-but-**Google-only** figures are the audit-relevant finding.
Filenames do not disclose backend, so content was verified directly rather than
inferred:

- `asymmetry_heatmap.png` — inspected: renders a **single "Google" column**,
  despite `data/results/nllb/round_trip.csv` existing.
- `chain_degradation_*.png` — inspected: **single row**, y-axis labelled
  "Google", despite `data/results/nllb/telephone_chain.csv` existing.
  Corroborated dimensionally: `figsize=(3.2·n_cols, 3.0·n_rows)` at dpi 160
  ⇒ 1 translator ≈ 480 px tall, 2 ⇒ ≈ 960 px. Measured height **516 px** ⇒
  `n_rows = 1`.
- `roundtrip_nllb.png` **does not exist** (17 Google vs 16 NLLB files).

**Root cause (verified, not inferred):** `scripts/make_figures.py:25-27` defaults
`--chain-csv` and `--roundtrip-csv` to `data/results/google/…`. The per-translator
and combined figures were produced by pointing `--long-csv` at
`combined_long.csv`, but the chain and round-trip inputs were left at their
Google defaults.

> **RESOLVED — the defaults now cover both backends.** `--chain-csv` and
> `--roundtrip-csv` are now `nargs="*"` lists whose defaults name *both*
> backends' CSVs, and `--long-csv` defaults to `combined_long.csv`. The paths
> live in `visualization/__init__.py:40-48` as `DEFAULT_LONG_CSV`,
> `DEFAULT_CHAIN_CSVS` and `DEFAULT_ROUNDTRIP_CSVS`; `run_all` concatenates
> however many chain / round-trip CSVs it is given, which is how both systems
> reach those figures. `scripts/make_figures.py:34-41` binds the flags to them.
>
> ```bash
> grep -n "nargs\|DEFAULT_" scripts/make_figures.py
> # 36:    p.add_argument("--chain-csv", nargs="*", default=list(DEFAULT_CHAIN_CSVS),
> # 39:    p.add_argument("--roundtrip-csv", nargs="*", default=list(DEFAULT_ROUNDTRIP_CSVS),
> ```
>
> The three per-backend consequences above are gone: `asymmetry_heatmap.png`
> renders one column per system, `chain_degradation_*.png` one row per system,
> and `roundtrip_nllb.png` exists.

**Consequence for README line 70-75** ("Regenerate **every** figure from the
committed result CSVs … `python scripts/make_figures.py`"): **WRONG as written.**
That bare command reads Google-only CSVs and would regenerate only Google
figures — it cannot reproduce the 16 NLLB figures or the 7 combined ones. The
runtime estimate "~30 seconds" is **UNVERIFIED** (figures were deliberately not
regenerated, to avoid overwriting committed artifacts).

> **RESOLVED — the bare command is now correct.** `python scripts/make_figures.py`
> with no arguments reproduces the full committed set: all 52 files, verified
> rewritten in a single run with no errors or warnings. The figure count went
> **43 → 52**; the nine new files are `roundtrip_nllb.png`,
> `chain_degradation_{cosine,bleu,ter}_{google,nllb}.png` and
> `asymmetry_heatmap_{google,nllb}.png`. The three unsuffixed
> `chain_degradation_*.png` and `asymmetry_heatmap.png` kept their filenames but
> are now two-system comparison figures rather than Google-only, so no committed
> path was orphaned.
>
> The **"~30 seconds" estimate remains UNVERIFIED** — the regeneration was not
> timed, so there is still no measurement to check it against. (The reason has
> changed: figures *have* now been regenerated; they simply were not timed. The
> README no longer states any runtime estimate, so nothing currently depends on
> this figure.)

**Additional contradiction:** `scatter_cosine_vs_bleu.png` displays
**"Pearson r = 0.814"**, because it pools both backends (n=540). The README text
states r = 0.651 (Google, n=270). Both are correct for their own scope, but the
committed figure and the README prose visibly disagree, with nothing on either
to explain why.

```bash
python -c "
import pandas as pd; from scipy import stats
c=pd.read_csv('data/results/combined_long.csv')
print('pooled n=%d r=%.4f'%(len(c), stats.pearsonr(c.cosine,c.bleu)[0]))"
# pooled n=540 r=0.8142     ← matches the 0.814 printed in the PNG
```

> **RESOLVED — the scatter is now split per system.** `scatter_*.png` renders one
> panel per translation system, each annotated with its own *r*, *p* and *n*, and
> each with its own OLS fit. The Google panel now prints **r = 0.651, n = 270**,
> which is exactly the value the README quotes, so figure and prose agree. The
> pooled statistic is no longer silently substituted: it appears as an explicit
> footnote, "Panels are separate populations. Pooled across both systems:
> r = 0.814 (n = 540)". Both numbers are now visible with their scopes attached.
> No computed value changed — 0.6505 and 0.8142 are the same quantities verified
> above, only differently disclosed.

`figures/README.md` is **STALE**: it states figures come from
`data/results/google/back_translation_long.csv` (line 3-4), describes the second
translator as pending ("currently only Google; the second translator will appear
once NLLB is run", line 36-37), marks telephone-chain and round-trip plots
"*(forthcoming)*" (lines 76, 86) though both exist, and lists only the `_google`
variants of every per-translator figure.

> **RESOLVED — `figures/README.md` was rebuilt from the directory contents.**
> It was in fact staler than this finding recorded: it listed **21 of 52**
> figures, omitting not just the nine new ones but *every* `_nllb` variant
> (`heatmap_nllb_*`, `bar_family_*_nllb`, `boxplot_*_nllb`, `radar_nllb`,
> `corr_matrix_nllb`). The rebuild was done against `git ls-files figures` plus
> the untracked new files rather than the old list, and verified group-by-group
> against the 52 files on disk.
>
> All four original points are fixed: the input is now `combined_long.csv` plus
> both backends' chain and round-trip CSVs, the "second translator will appear
> once NLLB is run" line is gone, both *(forthcoming)* headings are gone, and
> every per-translator figure is listed for both backends. The two further
> discrepancies noted above are also fixed: the per-family heatmaps are now
> described as **2×2** (matching what they became), and all nine new figures are
> listed. Every section is tagged with the backend(s) it covers, with a
> 21 / 21 / 10 coverage table at the top.
>
> With this, **every finding in §8 is resolved.**

---

## 9. `git remote -v` vs README clone URL and BibTeX URL

**They still disagree. The earlier fix was applied to the BibTeX only.**

```bash
git remote -v
# origin  https://github.com/danjack0/translation-fidelity-atlas.git (fetch)
# origin  https://github.com/danjack0/translation-fidelity-atlas.git (push)

grep -n "github.com" README.md
# 63:git clone https://github.com/danjackdev/translation-fidelity-atlas.git
# 164:  url    = {https://github.com/danjack0/translation-fidelity-atlas}
```

| Location | URL | Matches remote? |
|---|---|---|
| `git remote origin` | `danjack0/translation-fidelity-atlas` | — (authority) |
| README line 63 (clone) | **`danjackdev/…`** | **NO — WRONG** |
| README line 164 (BibTeX) | `danjack0/…` | **YES — OK** |

Commit `0d5f87c` ("Update author name and URL in README.md") changed **only the
BibTeX block** — it rewrote `danjackdev` → `danjack0` and `Jack, Daniel` →
`Jackson, Daniel` inside the `@misc` entry, and touched nothing else:

```bash
git show 0d5f87c -- README.md
# -  author = {Jack, Daniel}
# +  author = {Jackson, Daniel}
# -  url    = {https://github.com/danjackdev/translation-fidelity-atlas}
# +  url    = {https://github.com/danjack0/translation-fidelity-atlas}
```

**The `danjackdev`/`danjack0` mismatch is therefore NOT fully fixed** — the
clone command on line 63 was missed and still points at a different account. As
committed, the quick-start `git clone` is the one command in the README a new
user runs first, and it will fail unless `danjackdev/translation-fidelity-atlas`
also exists (**UNVERIFIED** — checking would require a network call, which is out
of scope for this read-only audit).

Related identity facts (consistent, no action needed): `LICENSE` reads
"Copyright (c) 2026 Daniel Jackson" (fixed in `0b5fb05`), matching the BibTeX
author `Jackson, Daniel`. The git commit author is `danjack0
<danche.j.1018@gmail.com>`.

> **RESOLVED in the README — STILL OPEN in `pyproject.toml`.** The README's
> clone command now reads `danjack0`, matching both its own BibTeX entry and
> `git remote -v`, and the BibTeX key was changed to `jackson2026fidelity`.
>
> Re-checking this finding across the whole repo, rather than the README alone,
> surfaces two survivors that the original §9 did not examine — `pyproject.toml`
> was out of its scope:
>
> ```bash
> grep -n "github.com\|authors" pyproject.toml
> # 12:authors = [{ name = "Daniel Jack" }]
> # 57:Repository = "https://github.com/danjackdev/translation-fidelity-atlas"
> ```
>
> * **`pyproject.toml:57`** still points `Repository` at `danjackdev`, the exact
>   mismatch this section documents, in a second file.
> * **`pyproject.toml:12`** names the author **"Daniel Jack"**, against
>   "Daniel Jackson" in both `LICENSE` and the BibTeX entry. This is the same
>   `Jack` → `Jackson` correction commit `0d5f87c` applied to the README's
>   BibTeX and nowhere else.
>
> Both are package metadata, not documentation, and neither has been changed —
> they are the only open items in this audit. Whether `github.com/danjackdev/…`
> resolves remains **UNVERIFIED**; it would still require a network call.

---

## Appendix A — README claims verified as correct

Beyond the 13 Google statistics in §6g:

| Claim (line) | Verified | Source |
|---|---|---|
| "45 languages across 8 typological families", "6 content domains" (3-5) | 45 / 8 / 6, both backends | §3 |
| Family sizes 7/7/9/3/3/9/4/3 = 45 (130-133) | exact match to `config.py` | §3 |
| "three protocols" (5-6) | back-translation, chain, round-trip — all 3 present for both backends | §4 |
| "five-hop telephone chains" (5) | 5 measured hops + synthetic hop 0 | §4 |
| "two translation systems" (6-7) | google, nllb | §3 |
| "four fidelity metrics" (7-8) | `METRICS = ['cosine','bleu','ter','embedding']` | `config.py:66` |
| BLEU and TER "via `sacrebleu`" (134) | `sacrebleu.corpus_bleu` / `corpus_ter` | `scoring/lexical.py:20,52,57` |
| spaCy `en_core_web_md` cosine (135) | `spacy.load("en_core_web_md")` | `scoring/lexical.py:27` |
| sentence-transformer `all-MiniLM-L6-v2` (136) | default model name | `scoring/semantic.py:21` |
| "MD5-keyed cache" (120) | `hashlib.md5(f"{translator}\|{src}\|{tgt}\|{text}")` | `cache.py:27-30` |
| corpora "6 domains × ~100 sentences" (116) | exactly 100 each, 600 total | §3 |
| "NLLB checkpoint is fixed and reproducible" (145-146) | `facebook/nllb-200-distilled-600M` pinned | `translators/nllb.py:82` |
| "One row per (translator × language × domain), 270 rows" (117) | 270 | §2 |
| wide CSV "one row per (translator × language)" (118) | 45 rows per backend | §2 |
| `make_figures.py` makes no API calls (70-71) | "Does not call any translator" — consumes CSVs only | `scripts/make_figures.py:5-6` |

## Appendix B — Corrections needed in README.md

Ordered by severity.

> **Status (post-audit): all ten items are now done.** This is the to-do list as
> it stood at `7d20fa2`; the list below is left as written so the original
> findings stay visible.
>
> * **Items 1, 2, 5, 6, 7, 8** — done in the README rewrite, which reframed the
>   project as a two-system study.
> * **Item 3** — done in all three places: the README, `data/README.md` and
>   `docs/methodology.md` now all state 141,088 unique cached translations /
>   8.09 MB, worded as `len(cache)`.
> * **Items 4 and 9** — done by closing the figure gap and regenerating (§8).
> * **Item 10** — done: `figures/README.md` was rebuilt against the actual
>   directory contents (§8).
>
> One item **outside** this list is still open, and it is not a README
> correction: `pyproject.toml:57` still points `Repository` at
> `github.com/danjackdev/…` rather than the `danjack0` remote — the same
> mismatch §9 found in the README, in a file §9 did not examine. See §9.

1. **Line 29-35** — scope the form/meaning paragraph to Google, or rewrite it.
   Its central BLEU claim reverses under NLLB (§7c), and the "idiomatic and
   cultural are worst on both metrics" sentence is wrong for both backends (§7d).
2. **Line 63** — `danjackdev` → `danjack0` to match the remote and the BibTeX (§9).
3. **Lines 52, 85** — `54k`/`54,025`/`3 MB` → **141,088 entries, 8.09 MB**
   (§1). Same fix needed in `data/README.md:93` and `docs/methodology.md:150`.
4. **Line 70-75** — the bare `python scripts/make_figures.py` does not
   regenerate every figure; document the `--long-csv/--chain-csv/--roundtrip-csv`
   invocations actually used (§8).
5. **Lines 51, 112-121** — document `data/results/nllb/` (7 files) and
   `data/results/combined_long.csv` (§2, §4).
6. **Lines 99-107** — NLLB ran all three protocols, not just back-translation;
   show the chain and round-trip commands too (§4).
7. **Add an NLLB headline section.** The repo now supports a genuine
   cross-system replication result — family replicates (ρ = +0.90), domain does
   not (ρ = +0.09) — which is a stronger contribution than either backend alone
   and is currently entirely absent from the README (§7).
8. **Optional (§6b)** — note that "family dominates domain" is a surface-form
   (BLEU/TER) result; it inverts on Google's embedding metric and NLLB's cosine.
9. **Optional (§8)** — `scatter_cosine_vs_bleu.png` shows r = 0.814 (pooled)
   while the text says 0.651 (Google); label the figure or regenerate per-backend.
10. **Optional (§8)** — `figures/README.md` still describes NLLB, chain, and
    round-trip figures as forthcoming.

## Appendix C — Items flagged UNVERIFIED

| Item | Why |
|---|---|
| "cache misses are ~0.3 s each" (line 88) | Requires live API calls — out of scope. **Moot:** the README no longer makes any per-miss timing claim |
| "~30 seconds" to regenerate figures (line 71) | **Still UNVERIFIED.** Figures *have* since been regenerated, but the run was not timed, so there is no measurement to check against. The README no longer states any runtime estimate, so nothing depends on it (§8) |
| Whether `github.com/danjackdev/…` resolves | Requires a network call. Still relevant: the README no longer uses that URL, but `pyproject.toml:57` does (§9) |
| Provenance of the exact figure `54,025` | Matches no cache state at any commit; Google back-translation alone is 54,000 |
| "The free Google Translate endpoint changes silently" (143-144) | Claim about external service behaviour; not checkable from artifacts. Still stated in the README's Limitations |
| Corpora are "author-curated (one writer)" (147-148) | No authorship metadata in the repo. Still stated in the README's Limitations and `docs/findings.md §7` |
| `hr` legal BLEU = 7.19 under NLLB — genuine or data-quality issue | Diagnosis would require re-running/inspecting translations |

---

*Audit performed read-only. No commits, no API calls, no retraining, no
experiment re-runs, no figure regeneration.*
