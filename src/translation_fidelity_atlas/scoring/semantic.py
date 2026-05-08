"""
Semantic similarity via sentence-transformer embeddings.

Unlike :mod:`.lexical`, this metric is largely insensitive to surface form.
Two sentences that say the same thing with different words score high here,
but score lower on BLEU / TER. The two metric families together let us
distinguish *form-preserving* from *meaning-preserving* translations — a
distinction that turns out to be central to interpreting our results.

Default model: ``all-MiniLM-L6-v2`` (22 M parameters, 384-dim, fast).
"""

from __future__ import annotations

from functools import lru_cache

from sklearn.metrics.pairwise import cosine_similarity


@lru_cache(maxsize=1)
def _sbert_model(model_name: str = "all-MiniLM-L6-v2"):
    """Load the sentence-transformer once and cache it."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_name)


def embedding_similarity(
    originals: list[str],
    candidates: list[str],
    batch_size: int = 64,
) -> float:
    """
    Mean pairwise cosine similarity over sentence-transformer embeddings.

    Both lists are encoded together in one batch to amortize tokenizer
    overhead. The diagonal of the resulting cosine-similarity matrix is the
    pairwise similarity between corresponding sentences.
    """
    if not originals:
        return 0.0
    sbert = _sbert_model()
    all_texts = list(originals) + list(candidates)
    embeds = sbert.encode(all_texts, batch_size=batch_size, show_progress_bar=False)
    o_e = embeds[: len(originals)]
    c_e = embeds[len(originals):]
    return float(round(cosine_similarity(o_e, c_e).diagonal().mean(), 6))
