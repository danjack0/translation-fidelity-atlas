"""
NLLB-200 backend, served locally via Hugging Face transformers.

Why NLLB?
---------
Google Translate is a closed, continuously-updated commercial system. NLLB-200
("No Language Left Behind", Meta AI, 2022) is an open research model with
known training data, known architecture, and a fixed checkpoint. Comparing
the two converts this study from "how good is Google" into "where do a
production system and a research baseline diverge", which is a much sharper
research question.

The first call downloads the model (~2.4 GB for the 600M-distilled variant,
~5 GB for the 1.3 B variant). After that, the model lives in your Hugging
Face cache and inference is offline.

Hardware
--------
* CPU works for the 600M variant but is slow (~2 s per sentence).
* A consumer NVIDIA GPU (8 GB) will run the 1.3 B variant comfortably.
* Apple Silicon: ``device="mps"`` works with ``torch >= 2.1``.

Language codes
--------------
NLLB uses BCP-47-style codes with a script subtag (``"eng_Latn"``,
``"jpn_Jpan"``, ``"zho_Hans"``). We accept the short ISO codes used elsewhere
in this project (``"en"``, ``"ja"``, ``"zh-CN"``) and translate them via
:data:`ISO_TO_NLLB`.
"""

from __future__ import annotations

import logging

from .base import Translator

log = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Short-ISO  →  NLLB code mapping for every language used in this project.    #
# --------------------------------------------------------------------------- #

ISO_TO_NLLB: dict[str, str] = {
    # Romance
    "it": "ita_Latn", "es": "spa_Latn", "fr": "fra_Latn", "pt": "por_Latn",
    "ro": "ron_Latn", "ca": "cat_Latn", "gl": "glg_Latn",
    # Germanic
    "de": "deu_Latn", "nl": "nld_Latn", "sv": "swe_Latn", "da": "dan_Latn",
    "no": "nob_Latn", "af": "afr_Latn", "is": "isl_Latn",
    # Slavic
    "ru": "rus_Cyrl", "pl": "pol_Latn", "cs": "ces_Latn", "uk": "ukr_Cyrl",
    "bg": "bul_Cyrl", "sr": "srp_Cyrl", "hr": "hrv_Latn", "sk": "slk_Latn",
    "sl": "slv_Latn",
    # Semitic
    "ar": "arb_Arab", "iw": "heb_Hebr", "mt": "mlt_Latn",
    # East Asian
    "zh-CN": "zho_Hans", "ja": "jpn_Jpan", "ko": "kor_Hang",
    # South & SE Asian
    "hi": "hin_Deva", "bn": "ben_Beng", "ur": "urd_Arab", "ta": "tam_Taml",
    "te": "tel_Telu", "th": "tha_Thai", "vi": "vie_Latn", "id": "ind_Latn",
    "ms": "zsm_Latn",
    # Turkic
    "tr": "tur_Latn", "az": "azj_Latn", "kk": "kaz_Cyrl", "uz": "uzn_Latn",
    # Uralic
    "fi": "fin_Latn", "et": "est_Latn", "hu": "hun_Latn",
    # Pivot
    "en": "eng_Latn",
}


class NLLBTranslator(Translator):
    """
    NLLB-200 served locally.

    The model and tokenizer are loaded lazily on the first call to
    :meth:`translate`, so importing this module is cheap.
    """

    name = "nllb"

    DEFAULT_MODEL = "facebook/nllb-200-distilled-600M"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: str | None = None,
        max_length: int = 256,
    ) -> None:
        self.model_name = model_name
        self.device = device  # resolved lazily so import works without torch
        self.max_length = max_length
        self._tokenizer = None
        self._model = None

    # ------------------------------------------------------------------ #

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return

        # Lazy imports keep the rest of the package importable on machines
        # where torch / transformers aren't installed.
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        if self.device is None:
            if torch.cuda.is_available():
                self.device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"

        log.info("Loading %s on %s ...", self.model_name, self.device)
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = (
            AutoModelForSeq2SeqLM.from_pretrained(self.model_name).to(self.device)
        )
        self._model.eval()

    # ------------------------------------------------------------------ #

    @staticmethod
    def _to_nllb(code: str) -> str:
        if code not in ISO_TO_NLLB:
            raise KeyError(
                f"Language code {code!r} is not in the NLLB mapping. "
                f"Add it to ISO_TO_NLLB in nllb.py."
            )
        return ISO_TO_NLLB[code]

    def translate(self, text: str, src: str, tgt: str) -> str:
        if not text:
            return text

        self._ensure_loaded()
        import torch  # already pulled in by _ensure_loaded

        src_nllb = self._to_nllb(src)
        tgt_nllb = self._to_nllb(tgt)

        self._tokenizer.src_lang = src_nllb
        inputs = self._tokenizer(
            text, return_tensors="pt", truncation=True, max_length=self.max_length
        ).to(self.device)

        # transformers >= 4.40 deprecates `lang_code_to_id`; use convert_tokens_to_ids
        forced_bos = self._tokenizer.convert_tokens_to_ids(tgt_nllb)

        with torch.no_grad():
            out = self._model.generate(
                **inputs,
                forced_bos_token_id=forced_bos,
                max_length=self.max_length,
                num_beams=4,
            )
        return self._tokenizer.batch_decode(out, skip_special_tokens=True)[0]
