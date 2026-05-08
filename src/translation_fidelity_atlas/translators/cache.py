"""
Disk-backed translation cache.

Translations are deterministic for a given ``(translator, src, tgt, text)``
tuple, so we cache them by an MD5 of that tuple. The cache survives across
runs and is the single biggest factor in keeping experiment cost reasonable —
a full re-run of the back-translation experiment hits the API for only the
cells that haven't been seen before.

The cache is stored as a single JSON file, optionally gzip-compressed
(``translation_cache.json.gz``). The gzipped form is ~6× smaller and is the
default for committing to a repository.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)


def cache_key(text: str, src: str, tgt: str, translator: str) -> str:
    """Stable hash for one translation request."""
    raw = f"{translator}|{src}|{tgt}|{text}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def load_cache(path: str | os.PathLike) -> dict[str, str]:
    """
    Load the cache, transparently handling either ``.json`` or ``.json.gz``.

    Returns an empty dict if the file does not exist.
    """
    path = Path(path)
    if path.suffix == ".gz" or str(path).endswith(".json.gz"):
        if not path.exists():
            log.info("No cache at %s, starting fresh", path)
            return {}
        with gzip.open(path, "rt", encoding="utf-8") as f:
            cache = json.load(f)
    else:
        if not path.exists():
            log.info("No cache at %s, starting fresh", path)
            return {}
        with path.open("r", encoding="utf-8") as f:
            cache = json.load(f)
    log.info("Loaded translation cache: %d entries from %s", len(cache), path)
    return cache


def save_cache(cache: dict[str, str], path: str | os.PathLike) -> None:
    """
    Persist the cache. Compression is inferred from the suffix.

    Writes to a sibling ``.tmp`` file first and atomically renames, so an
    interrupted run cannot corrupt an existing cache.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")

    if path.suffix == ".gz" or str(path).endswith(".json.gz"):
        with gzip.open(tmp, "wt", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
    else:
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

    tmp.replace(path)
    log.debug("Cache saved (%d entries) → %s", len(cache), path)
