# NLLB-200 setup

NLLB-200 is the second translation backend supported by this project. Unlike
the Google Translate backend, NLLB runs **locally** — no API keys, no rate
limits, but it does need to fit in your machine's memory and run inference.

## Why NLLB?

* **Reproducible.** Fixed checkpoint, frozen weights, known training data
  — anyone with the same model id will get the same results forever.
* **Offline after first run.** Once the model is downloaded to your
  Hugging Face cache (~3 GB for 600M-distilled, ~5 GB for 1.3B), subsequent
  runs are entirely local.
* **Open weights, open paper.** The contrast with Google Translate's
  black-box behaviour is part of what we're studying.

## Install

```bash
pip install -e .[nllb]
```

This installs the optional extras `torch`, `transformers`, and
`sentencepiece` on top of the base dependencies.

## Run

The default model is the 600M-parameter distilled variant — the smallest
NLLB-200, fast enough to use on CPU:

```bash
python scripts/run_back_translation.py --translator nllb
```

For the larger 1.3B variant (better quality, GPU strongly recommended):

```bash
python scripts/run_back_translation.py \
    --translator nllb \
    --nllb-model facebook/nllb-200-1.3B
```

Telephone-chain and round-trip experiments take the same flags:

```bash
python scripts/run_telephone_chain.py --translator nllb
python scripts/run_round_trip.py      --translator nllb
```

## Hardware

Approximate per-sentence inference time, beam = 4, max length = 256:

| Hardware | 600M-distilled | 1.3B |
|---|---|---|
| CPU (modern laptop)            | ~1.5–3 s | ~6–10 s |
| Apple Silicon (M1/M2/M3, MPS)  | ~0.4–0.8 s | ~1.5–2.5 s |
| NVIDIA RTX 3060 / 4060         | ~0.15 s | ~0.4 s |
| NVIDIA A100 / H100             | ~0.05 s | ~0.1 s |

The full back-translation experiment is ~12,150 sentences (45 languages × 6
domains × 100 sentences × 2 directions for the round trip — minus cache
hits). At 0.5 s per sentence that's roughly 100 minutes. The cache is
shared with Google Translate by `(translator, src, tgt, text)` key, so
NLLB's run does not benefit from existing Google cache entries — it builds
its own.

## Device selection

The backend picks a device automatically:

1. CUDA if available (`torch.cuda.is_available()`).
2. Apple Silicon Metal (`mps`) if `torch.backends.mps.is_available()`.
3. CPU otherwise.

Override with the `device` argument when constructing
`NLLBTranslator(device="cpu")` directly, or by editing
[`src/translation_fidelity_atlas/translators/nllb.py`](../src/translation_fidelity_atlas/translators/nllb.py).

## Apple Silicon notes

* Requires `torch >= 2.1`. Earlier versions have known issues with the
  forced-BOS token generation NLLB uses for target-language selection.
* MPS does not support `bfloat16` for some ops; the default `float32`
  inference path works.

## Language coverage

This project uses 45 target languages plus English; every one of them is
in the NLLB-200 supported set. The `ISO_TO_NLLB` map in
[`translators/nllb.py`](../src/translation_fidelity_atlas/translators/nllb.py)
contains the full short-ISO → NLLB BCP-47-with-script mapping. Adding a new
language means adding one entry to that dict.

## Disk usage

| Model | On-disk size (HF cache) |
|---|---|
| `facebook/nllb-200-distilled-600M` | ~2.4 GB |
| `facebook/nllb-200-1.3B`           | ~5.1 GB |
| `facebook/nllb-200-3.3B`           | ~13 GB  |

Models live in `~/.cache/huggingface/hub/`. Delete that directory to
reclaim space; the model will be re-downloaded on next use.

## Sanity check

After install, verify the NLLB pipeline is wired up correctly:

```python
from translation_fidelity_atlas.translators import get_translator
nllb = get_translator("nllb")
print(nllb.translate("The deployment pipeline runs on every commit.",
                     src="en", tgt="de"))
```

Expected output (subject to model variant): a fluent German rendering. If
this step works, every other CLI works.
