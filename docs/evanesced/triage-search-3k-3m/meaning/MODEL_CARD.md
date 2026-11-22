---
license: mit
base_model: BAAI/bge-small-en-v1.5
language:
- en
library_name: onnxruntime
tags:
- onnx
- int8
- sentence-similarity
- text-classification
---

# lastbook-meaning-red

The files behind Lastbook's meaning check for questions that may be urgent: an int8 copy of
[BAAI/bge-small-en-v1.5](https://huggingface.co/BAAI/bge-small-en-v1.5) and 31 centroid vectors. Lastbook is an offline
library app; this check runs on the person's own computer and sends nothing anywhere.

## Files

| File | What it is |
|---|---|
| `model_int8.onnx` | bge-small-en-v1.5's ONNX export, dynamically quantized to int8 with `onnxruntime.quantization.quantize_dynamic` (weights QInt8, default settings, nothing else changed). 32 MB. |
| `tokenizer.json` | bge-small-en-v1.5's tokenizer, unchanged. |
| `centroids.npz` | `red` (20 x 384) and `nonred` (11 x 384) unit vectors, float16, one per category of Lastbook's own invented examples; `red_categories`, `nonred_categories`; the thresholds `strict` and `wide`. |

SHA-256 and sizes: Lastbook's `engine/data/meaning_red_manifest.json`. The app checks every file against it before use.
All three can be rebuilt with Lastbook's `tools/meaning_red_model.py` from the original fp32 ONNX model.

## How Lastbook uses it

A question, after Lastbook's own spelling correction and with no query prefix, is embedded (the [CLS] vector, unit length,
at most 320 tokens). Its score is its highest cosine to a red centroid minus its highest cosine to a non-red one. Above the
`wide` threshold (0.00663) the question counts as possibly urgent.

It is only ever used to **add** to Lastbook's word rules (urgent = words OR meaning), never to remove a flag and never on
its own. An urgent flag in Lastbook only means the library pages found for the question are always shown.

The centroids come from 689 short sentences written for this purpose (315 urgent ones in 20 categories such as not
breathing, choking, bleeding, stroke, overdose, suicide; 144 "yellow" ones; 230 look-alikes such as idioms, cooking,
sport and first-aid course questions). The threshold was set on those examples only, out of fold.

## Not for

- **Not a medical device or a triage tool.** It cannot say whether someone is in danger. In an emergency, call your local
  emergency number.
- Not for use alone: on Lastbook's held-out test lists it finds about 84% of urgent lines by itself, and it flags about a
  quarter of everyday look-alike questions.
- English only. Other languages are caught or missed by chance.

## Limitations

The examples and the test lists were all written by the same AI model family; shared habits of phrasing make the
measured numbers optimistic for real people's messages. Everyday questions about children and old people, and idioms
the examples lack, are flagged too often.

## Licence

MIT, as bge-small-en-v1.5 (BAAI, per its model card). The centroids and examples are Lastbook's own, also MIT.

```
MIT License

Copyright (c) BAAI (Beijing Academy of Artificial Intelligence)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

## Citation

The base model: Xiao et al., "C-Pack: Packaged Resources To Advance General Chinese Embedding" (2023), and
https://huggingface.co/BAAI/bge-small-en-v1.5.
