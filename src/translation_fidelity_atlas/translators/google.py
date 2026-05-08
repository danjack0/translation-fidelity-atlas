"""
Google Translate backend, via :mod:`deep_translator`.

The free Google Translate endpoint has informal per-IP rate limits but no
hard daily cap. The ``delay`` argument on the higher-level batch helpers
exists primarily to keep us under the radar of those limits.
"""

from __future__ import annotations

import logging

from deep_translator import GoogleTranslator as _Google

from .base import Translator

log = logging.getLogger(__name__)


class GoogleTranslateBackend(Translator):
    """Thin wrapper around ``deep_translator.GoogleTranslator``."""

    name = "google"

    def translate(self, text: str, src: str, tgt: str) -> str:
        if not text:
            return text
        return _Google(source=src, target=tgt).translate(text)
