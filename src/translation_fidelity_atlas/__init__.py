"""
translation-fidelity-atlas
==========================

A multi-system, multi-family, multi-domain back-translation fidelity benchmark.

Top-level submodules
--------------------
* :mod:`.config`        — language families, domains, metrics, palette
* :mod:`.translators`   — Google Translate and NLLB-200 backends + cache
* :mod:`.scoring`       — cosine / BLEU / TER / embedding similarity
* :mod:`.experiments`   — back-translation, telephone-chain, round-trip
* :mod:`.visualization` — every figure the project produces
* :mod:`.analysis`      — ANOVA, effect sizes, summary tables
"""

__version__ = "0.1.0"
