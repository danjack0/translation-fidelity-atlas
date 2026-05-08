"""
Abstract translator interface.

All translation backends — Google Translate (API), NLLB-200 (local) and any
future system — implement :class:`Translator`. The protocol is intentionally
minimal: take a string and a language pair, return a string. Caching, retry,
and parallelism live in :mod:`translation_fidelity_atlas.experiments`,
not here.
"""

from __future__ import annotations

import abc


class Translator(abc.ABC):
    """
    Single-string translation backend.

    Subclasses must implement :meth:`translate`. The class attribute
    :attr:`name` is used as the cache namespace and as a key in result CSVs;
    pick something short and lowercase, e.g. ``"google"``, ``"nllb"``.
    """

    #: Short identifier used in CSV outputs and the translation cache.
    name: str = "abstract"

    @abc.abstractmethod
    def translate(self, text: str, src: str, tgt: str) -> str:
        """
        Translate ``text`` from ``src`` to ``tgt``.

        Parameters
        ----------
        text
            Source string. Empty strings should round-trip unchanged.
        src, tgt
            ISO 639-1 language codes (``"en"``, ``"ja"``, ``"zh-CN"``).
            Each backend is responsible for mapping these to whatever format
            the underlying engine expects (NLLB needs e.g. ``"eng_Latn"``).

        Returns
        -------
        str
            The translated string. On unrecoverable failure, implementations
            are encouraged to raise rather than return junk — the experiment
            layer will retry, log, and decide how to fall back.
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={self.name!r}>"
