"""All four fidelity metrics in one importable namespace."""

from .lexical import bleu, cosine, ter
from .semantic import embedding_similarity


def all_metrics(originals: list[str], candidates: list[str]) -> dict[str, float]:
    """
    Compute every metric on one (originals, candidates) pair.

    Returns a dict with keys ``cosine``, ``bleu``, ``ter``, ``embedding`` —
    the canonical metric names used everywhere else in the project.
    """
    return {
        "cosine":    cosine(originals, candidates),
        "bleu":      bleu(originals, candidates),
        "ter":       ter(originals, candidates),
        "embedding": embedding_similarity(originals, candidates),
    }


__all__ = ["bleu", "cosine", "ter", "embedding_similarity", "all_metrics"]
