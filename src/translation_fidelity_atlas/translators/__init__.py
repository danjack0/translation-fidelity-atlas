"""Translation backends and the shared cache."""

from .base import Translator
from .cache import cache_key, load_cache, save_cache
from .google import GoogleTranslateBackend
from .nllb import NLLBTranslator

#: Registry mapping ``Translator.name`` → constructor.
#: New backends should register themselves here so they're addressable
#: from the CLI by short name.
REGISTRY: dict[str, type[Translator]] = {
    "google": GoogleTranslateBackend,
    "nllb":   NLLBTranslator,
}


def get_translator(name: str, **kwargs) -> Translator:
    """Construct a translator by short name (``"google"``, ``"nllb"``)."""
    if name not in REGISTRY:
        raise KeyError(f"Unknown translator {name!r}. Available: {list(REGISTRY)}")
    return REGISTRY[name](**kwargs)


__all__ = [
    "Translator",
    "GoogleTranslateBackend",
    "NLLBTranslator",
    "REGISTRY",
    "get_translator",
    "cache_key",
    "load_cache",
    "save_cache",
]
