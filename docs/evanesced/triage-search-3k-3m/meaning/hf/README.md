---
license: mit
base_model: BAAI/bge-small-en-v1.5
language:
- en
library_name: gguf
tags:
- gguf
- q8_0
- llama.cpp
- sentence-similarity
- text-classification
---

# lastbook-meaning-red

The files behind a meaning check for questions that may be urgent, used by a fork of
[Lastbook](https://github.com/Immortal-Protocols/lastbook) ([STAirye/lastbook](https://github.com/STAirye/lastbook)), an
offline library app. They are a q8_0 GGUF of [BAAI/bge-small-en-v1.5](https://huggingface.co/BAAI/bge-small-en-v1.5) and
31 centroid vectors. The check runs on the person's own computer and sends nothing anywhere.

## Files

| File | What it is |
|---|---|
| `bge-small-en-v1.5-q8_0.gguf` | bge-small-en-v1.5 converted with llama.cpp's own `convert_hf_to_gguf.py --outtype q8_0` (tag b12032), [CLS] pooling. 37 MB. Read by the app's llama.cpp runner in embedding mode. |
| `centroids.npz` | `red` (20 x 384) and `nonred` (11 x 384) unit vectors, float32, one per category of the fork's own invented examples; `red_categories`, `nonred_categories`; the thresholds `strict` and `wide`. No pickled objects. |

Sizes and SHA-256 are in the fork's `engine/data/meaning_red_manifest.json`, pinned to a commit of this repo. The app
checks every file against them before use. Both files can be rebuilt with the fork's `tools/meaning_red_model.py` from
the original model; the same inputs give the same bytes.

## How it is used

A question, after the app's own spelling correction and with no query prefix, is embedded (the [CLS] vector, unit
length, at most 320 tokens). Its score is its highest cosine to a red centroid minus its highest cosine to a non-red one.
Above the `wide` threshold (0.0084) the question counts as possibly urgent.

It is only ever used to **add** to the app's word rules (urgent = words OR meaning), never to remove a flag and never on
its own. In the app an urgent flag only means the library pages found for the question are always shown.

The centroids come from 689 short sentences written for this purpose: 315 urgent ones in 20 categories (not breathing,
choking, bleeding, stroke, overdose, suicide and others), 144 "yellow" ones, and 230 look-alikes (idioms, cooking, sport,
first-aid course questions and others). The thresholds were set on those examples only, out of fold.

## How to read the numbers

The app treats urgency like a screening step, not a diagnosis: a miss costs far more than a false alarm, and a false
alarm is cheap (the pages found are shown anyway, with emergency buttons; nothing is withheld). So the rule is tuned for
sensitivity and accepts low specificity. A useful reference is trauma field triage. The American College of Surgeons
Committee on Trauma sets a goal of under 5% undertriage (*Resources for Optimal Care of the Injured Patient*, 2014), and
"most agree that an acceptable percentage of overtriage is in the range of 25 to 35 percent" (same, chapter 3, p. 28).

On the three held-out lists (an urgent line not flagged = undertriage; an everyday line flagged = overtriage):

| | Urgent caught | Undertriage | Everyday flagged |
|---|---|---|---|
| This check alone | 81–87% | 13–19% | 25–30% |
| The app's words OR this check | 99.4% / 97.6% / 94.5% | 0.6% / 2.4% / 5.5% | 43% / 60% / 68% |

Alone, this check is not sensitive enough to screen with, which is why it only adds to the word rules. Combined, the
undertriage goal is met on two lists and narrowly missed on the third. Overtriage is above that range, but the everyday
lines were written to be hard look-alikes and mild symptoms, not a random sample of questions.

## Not for

- **Not a medical device or a triage tool.** It cannot say whether someone is in danger. In an emergency, call your local
  emergency number.
- Not for use alone. On three held-out test lists it found 81–87% of urgent lines by itself, and flagged 25–30% of
  everyday look-alike questions.
- English only. Other languages are caught or missed by chance.

## Limitations

The examples and the test lists were all written with AI help, from the same model family; shared habits of phrasing make
the measured numbers optimistic for real people's messages. Everyday questions about children and old people, and idioms
the examples lack, are flagged too often.

## Licence

MIT, as bge-small-en-v1.5 (BAAI, per its model card); see `LICENSE`. The centroids and examples are the fork's own, also
MIT.

## Citation

The base model: Xiao et al., "C-Pack: Packaged Resources To Advance General Chinese Embedding" (2023), and
https://huggingface.co/BAAI/bge-small-en-v1.5.
