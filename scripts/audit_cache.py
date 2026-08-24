"""Read-only cache attribution: replay every protocol's key derivation
against the committed corpora and cache. No network, no model calls.

Cache keys are md5(f"{translator}|{src}|{tgt}|{text}"), so a key alone does
not reveal its backend. But every key is *derivable*: forward keys come from
the committed corpora, and each forward value supplies the text for the next
hop's key. Walking that chain attributes keys to (backend, protocol).
"""
import gzip
import hashlib
import json
from collections import defaultdict

from translation_fidelity_atlas.config import (
    CHAIN_ORDER_LINGUISTIC,
    CHAIN_ORDERS,
    DOMAINS,
    LANGUAGE_FAMILIES,
)

LANGS = [l for fam in LANGUAGE_FAMILIES.values() for l in fam]
# scripts/run_round_trip.py --languages defaults to CHAIN_ORDER_LINGUISTIC
ROUND_TRIP_LANGS = CHAIN_ORDER_LINGUISTIC


def key(text, src, tgt, tr):
    return hashlib.md5(f"{tr}|{src}|{tgt}|{text}".encode("utf-8")).hexdigest()


with gzip.open("data/translation_cache.json.gz", "rt", encoding="utf-8") as f:
    cache = json.load(f)

corpora = {}
for d in DOMAINS:
    with open(f"data/corpora/{d}.txt", encoding="utf-8") as f:
        corpora[d] = [ln.rstrip("\n") for ln in f if ln.strip()]

# owner[key] = set of "backend:protocol" tags
owner = defaultdict(set)
missing = defaultdict(int)


def take(text, src, tgt, tr, tag):
    """Attribute one key; return its cached value or None if absent."""
    k = key(text, src, tgt, tr)
    if k in cache:
        owner[k].add(tag)
        return cache[k]
    missing[tag] += 1
    return None


for tr in ("google", "nllb"):
    # ---- Protocol 1: single-pivot back-translation (en -> L -> en) ----
    for lang in LANGS:
        for dom, sents in corpora.items():
            for s in sents:
                fwd = take(s, "en", lang, tr, f"{tr}:back_translation")
                if fwd is not None:
                    take(fwd, lang, "en", tr, f"{tr}:back_translation")

    # ---- Protocol 2: telephone chain (5 hops, + scoring detour to en) ----
    for order_name, chain in CHAIN_ORDERS.items():
        for dom, sents in corpora.items():
            cur, cur_lang = list(sents), "en"
            for tgt in chain:
                nxt = []
                for t in cur:
                    v = take(t, cur_lang, tgt, tr, f"{tr}:telephone_chain")
                    nxt.append(v if v is not None else t)
                cur, cur_lang = nxt, tgt
                for t in cur:
                    take(t, tgt, "en", tr, f"{tr}:telephone_chain")

    # ---- Protocol 3: round-trip ABA/BAB ----
    # scripts/run_round_trip.py picks the language list; resolved separately.
    for lang in ROUND_TRIP_LANGS:
        for dom, sents in corpora.items():
            for s in sents:
                fwd = take(s, "en", lang, tr, f"{tr}:round_trip")
                if fwd is None:
                    continue
                back = take(fwd, lang, "en", tr, f"{tr}:round_trip")
                if back is not None:
                    take(back, "en", lang, tr, f"{tr}:round_trip")

print("cache keys total:", len(cache))
print("attributed:", len(owner), " unattributed:", len(cache) - len(owner))

by_backend = defaultdict(set)
by_tag = defaultdict(set)
for k, tags in owner.items():
    for t in tags:
        by_tag[t].add(k)
        by_backend[t.split(":")[0]].add(k)

print("\n-- unique keys by backend --")
for b in sorted(by_backend):
    print(f"  {b:8s} {len(by_backend[b]):7d}")
gk, nk = by_backend.get("google", set()), by_backend.get("nllb", set())
print(f"  overlap google&nllb: {len(gk & nk)}")

print("\n-- unique keys by backend:protocol --")
for t in sorted(by_tag):
    print(f"  {t:28s} {len(by_tag[t]):7d}")

print("\n-- keys shared across protocols (same backend) --")
for b in ("google", "nllb"):
    bt = {t: v for t, v in by_tag.items() if t.startswith(b)}
    names = sorted(bt)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            ov = bt[names[i]] & bt[names[j]]
            if ov:
                print(f"  {names[i]} & {names[j]}: {len(ov)}")

print("\n-- lookups that MISSED the cache (would need an API call) --")
for t in sorted(missing):
    print(f"  {t:28s} {missing[t]:7d}")
