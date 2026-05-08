"""
Lexical / surface-form scoring metrics.

These metrics compare the **surface form** of the original and back-translated
text. They reward word-level overlap and penalize substitutions, deletions,
and insertions.

* :func:`cosine` — mean spaCy ``en_core_web_md`` cosine similarity, computed
  on word-vector averages. Ranges 0–1; a model is considered well-calibrated
  when this lies somewhere in 0.95–1.00 for round-trips.
* :func:`bleu`   — corpus-level BLEU via ``sacrebleu``. Ranges 0–100.
* :func:`ter`    — corpus-level Translation Edit Rate. *Lower is better.*
  Ranges 0+ (theoretically uncapped).
"""

from __future__ import annotations

from functools import lru_cache

import sacrebleu


@lru_cache(maxsize=1)
def _spacy_model():
    """Load the spaCy model once. Heavy import is deferred until first use."""
    import spacy
    return spacy.load("en_core_web_md")


def cosine(originals: list[str], candidates: list[str]) -> float:
    """
    Mean pairwise cosine similarity using spaCy's word-vector model.

    Empty vectors (``vector_norm == 0``) are scored as 0.0 rather than
    raising, which can happen for very short or all-OOV strings.
    """
    nlp = _spacy_model()
    if not originals:
        return 0.0
    sims = []
    for o, c in zip(originals, candidates):
        do, dc = nlp(o), nlp(c)
        if do.vector_norm and dc.vector_norm:
            sims.append(do.similarity(dc))
        else:
            sims.append(0.0)
    return round(sum(sims) / len(sims), 6)


def bleu(originals: list[str], candidates: list[str]) -> float:
    """Corpus-level BLEU. Higher is better; range 0–100."""
    return round(sacrebleu.corpus_bleu(candidates, [originals]).score, 4)


def ter(originals: list[str], candidates: list[str]) -> float:
    """Corpus-level Translation Edit Rate. **Lower is better**; 0+."""
    return round(sacrebleu.corpus_ter(candidates, [originals]).score, 4)
