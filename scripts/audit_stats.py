"""Recompute the README's headline statistics from the committed CSVs,
independently per backend. Read-only: no API calls, no retraining."""
import sys

import pandas as pd
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")

from translation_fidelity_atlas.analysis import one_way_anova  # noqa: E402


def report(df, label):
    print("=" * 72)
    print(f"{label}   (n = {len(df)} cells)")
    print("=" * 72)

    # --- ANOVA / eta-squared -------------------------------------------------
    print("\n-- one-way ANOVA on BLEU --")
    res = {}
    for factor in ("family", "domain"):
        r = one_way_anova(df, factor, "bleu")
        res[factor] = r
        print(f"  {factor:7s} eta2={r['eta_squared']:.4f}  F={r['F']:8.3f}  "
              f"p={r['p']:.3e}  df=({r['df_between']},{r['df_within']})")
    ratio = res["family"]["eta_squared"] / res["domain"]["eta_squared"]
    print(f"  family/domain eta2 ratio = {ratio:.2f}x")

    # same for the other metrics, to see if the story is BLEU-specific
    print("\n-- eta2 by factor, all metrics --")
    print(f'  {"metric":10s} {"family":>9s} {"domain":>9s} {"ratio":>7s}')
    for m in ("cosine", "bleu", "ter", "embedding"):
        f_ = one_way_anova(df, "family", m)["eta_squared"]
        d_ = one_way_anova(df, "domain", m)["eta_squared"]
        print(f"  {m:10s} {f_:9.4f} {d_:9.4f} {d_ and f_/d_:7.2f}")

    # --- correlations --------------------------------------------------------
    print("\n-- Pearson r vs BLEU --")
    for m in ("cosine", "embedding", "ter"):
        r, p = stats.pearsonr(df["bleu"], df[m])
        rs, _ = stats.spearmanr(df["bleu"], df[m])
        print(f"  bleu~{m:10s} r={r:+.4f} (p={p:.3e})  spearman={rs:+.4f}")
    r, p = stats.pearsonr(df["cosine"], df["embedding"])
    print(f"  cosine~embedding  r={r:+.4f} (p={p:.3e})")

    # --- per-family / per-domain means --------------------------------------
    print("\n-- mean BLEU by family --")
    fam = df.groupby("family")["bleu"].agg(["mean", "std", "count"]).sort_values("mean", ascending=False)
    for k, v in fam.iterrows():
        print(f"  {k:16s} {v['mean']:6.2f}  (sd {v['std']:5.2f}, n={int(v['count'])})")
    print(f"  BEST={fam.index[0]} ({fam['mean'].iloc[0]:.2f})  "
          f"WORST={fam.index[-1]} ({fam['mean'].iloc[-1]:.2f})  "
          f"gap={fam['mean'].iloc[0]-fam['mean'].iloc[-1]:.2f}")

    print("\n-- mean BLEU by domain --")
    dom = df.groupby("domain")["bleu"].agg(["mean", "std", "count"]).sort_values("mean", ascending=False)
    for k, v in dom.iterrows():
        print(f"  {k:16s} {v['mean']:6.2f}  (sd {v['std']:5.2f}, n={int(v['count'])})")
    print(f"  BEST={dom.index[0]} ({dom['mean'].iloc[0]:.2f})  "
          f"WORST={dom.index[-1]} ({dom['mean'].iloc[-1]:.2f})")

    print("\n-- mean COSINE by domain (form vs meaning check) --")
    dcos = df.groupby("domain")["cosine"].mean().sort_values(ascending=False)
    for k, v in dcos.items():
        print(f"  {k:16s} {v:.4f}")
    print("\n-- mean EMBEDDING by domain --")
    demb = df.groupby("domain")["embedding"].mean().sort_values(ascending=False)
    for k, v in demb.items():
        print(f"  {k:16s} {v:.4f}")

    print("\n  domain rank by BLEU   :", list(dom.index))
    print("  domain rank by COSINE :", list(dcos.index))
    print("  domain rank by EMBED  :", list(demb.index))
    tau, tp = stats.kendalltau(
        [list(dom.index).index(d) for d in dom.index],
        [list(dcos.index).index(d) for d in dom.index],
    )
    print(f"  Kendall tau (BLEU-rank vs COSINE-rank across 6 domains) = {tau:+.3f} (p={tp:.3f})")

    # --- extreme cells -------------------------------------------------------
    print("\n-- extreme single cells (BLEU) --")
    b = df.nlargest(3, "bleu")[["family", "language", "domain", "bleu"]]
    w = df.nsmallest(3, "bleu")[["family", "language", "domain", "bleu"]]
    print("  BEST:")
    for _, r in b.iterrows():
        print(f"    {r['language']:6s} {r['domain']:16s} {r['bleu']:6.2f}  ({r['family']})")
    print("  WORST:")
    for _, r in w.iterrows():
        print(f"    {r['language']:6s} {r['domain']:16s} {r['bleu']:6.2f}  ({r['family']})")

    # README-specific spot checks
    print("\n-- README spot checks --")
    gm = df[df.family == "germanic"].groupby("language")["bleu"].mean()
    for lg in ("da", "no", "sv"):
        tech = df[(df.language == lg) & (df.domain == "technical")]["bleu"]
        if len(tech):
            print(f"    {lg} technical BLEU = {tech.iloc[0]:.2f}   (>85? {tech.iloc[0] > 85})")
    th = df[(df.language == "th") & (df.domain == "legal")]["bleu"]
    if len(th):
        print(f"    th legal BLEU = {th.iloc[0]:.2f}")
    da = df[(df.language == "da") & (df.domain == "technical")]["bleu"]
    if len(da):
        print(f"    da technical BLEU = {da.iloc[0]:.2f}")
    print()
    return {"fam": fam, "dom": dom, "dcos": dcos, "res": res}


g = pd.read_csv("data/results/google/back_translation_long.csv")
n = pd.read_csv("data/results/nllb/back_translation_long.csv")
G = report(g, "GOOGLE")
N = report(n, "NLLB")

print("=" * 72)
print("CROSS-BACKEND AGREEMENT")
print("=" * 72)
m = g.merge(n, on=["family", "language", "domain"], suffixes=("_g", "_n"))
print(f"matched cells: {len(m)}")
for metric in ("bleu", "cosine", "ter", "embedding"):
    r, p = stats.pearsonr(m[f"{metric}_g"], m[f"{metric}_n"])
    rs, _ = stats.spearmanr(m[f"{metric}_g"], m[f"{metric}_n"])
    print(f"  cell-level {metric:10s} google~nllb  r={r:+.4f} (p={p:.2e}) rho={rs:+.4f}"
          f"   mean g={m[f'{metric}_g'].mean():6.2f} n={m[f'{metric}_n'].mean():6.2f}")

print("\n-- family mean BLEU side by side --")
fg, fn = G["fam"]["mean"], N["fam"]["mean"]
print(f'  {"family":16s} {"google":>8s} {"nllb":>8s} {"delta":>8s}')
for k in fg.index:
    print(f"  {k:16s} {fg[k]:8.2f} {fn[k]:8.2f} {fn[k]-fg[k]:+8.2f}")
rho, p = stats.spearmanr([fg[k] for k in fg.index], [fn[k] for k in fg.index])
print(f"  family-ranking Spearman rho = {rho:+.4f} (p={p:.4f})")
print(f"  google family order: {list(fg.index)}")
print(f"  nllb   family order: {list(fn.index)}")

print("\n-- domain mean BLEU side by side --")
dg, dn = G["dom"]["mean"], N["dom"]["mean"]
print(f'  {"domain":16s} {"google":>8s} {"nllb":>8s} {"delta":>8s}')
for k in dg.index:
    print(f"  {k:16s} {dg[k]:8.2f} {dn[k]:8.2f} {dn[k]-dg[k]:+8.2f}")
rho, p = stats.spearmanr([dg[k] for k in dg.index], [dn[k] for k in dg.index])
print(f"  domain-ranking Spearman rho = {rho:+.4f} (p={p:.4f})")
print(f"  google domain order: {list(dg.index)}")
print(f"  nllb   domain order: {list(dn.index)}")

print("\n-- combined_long.csv integrity --")
c = pd.read_csv("data/results/combined_long.csv")
cat = pd.concat([g, n], ignore_index=True)
key = ["translator", "family", "language", "domain"]
same = (c.sort_values(key).reset_index(drop=True)[cat.columns]
        .equals(cat.sort_values(key).reset_index(drop=True)))
print(f"  combined == google+nllb concatenated: {same}")
print(f"  combined rows={len(c)}  per-translator={c.translator.value_counts().to_dict()}")
