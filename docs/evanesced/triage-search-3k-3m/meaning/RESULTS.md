# Meaning-based red check: prototype and measurement (2026-11-19)

Prototype only, in this folder. Nothing in the repo was changed, nothing committed, nothing written to a data folder
(`LASTBOOK_DATA=D:\LastbookData-fork-test` read for the model and typo words only). Code at 19c2db2.

## What was done

**Phase A: examples, written first.** `make_examples.py` writes `examples.jsonl`: 315 red sentences in 20 categories
(not breathing, choking, unconscious, seizure, bleeding, chest pain, stroke, anaphylaxis, overdose/poisoning, suicide,
drowning, burns/electric, heat/cold, head/spine, childbirth, baby/child/elderly, sepsis, diabetic, other trauma,
non-native/slang), 144 yellow and 230 look-alike greens in 10 categories (idioms, tech, cooking/home, sport/games,
first-aid course questions, mild symptoms, everyday how-to, look-alike words, dark-humour figures of speech, noise).
Written from general knowledge before any test list was opened; `independent\`, `independent2\` and `triage\` were not
read until phase C. The current word rule on the examples: red 303/315, yellow 98/144, green 83/230.

**Phase B: method, chosen on the examples only** (`cv.py`, `cv_results.json`). Questions and examples go through
`typos.correct` first, then the same `retrieval.Embedder` (bge-small-en-v1.5 ONNX, CLS vector, unit length). Twelve
scorers, each with and without bge's query prefix, 5-fold x 3 stratified by category; the threshold is the score above
which 5% (strict) or 10% (wide) of the out-of-fold green examples fall. Red recall out of fold:

| method | at 5% green FP | at 10% |
|---|---|---|
| kNN vote k=3/5/7/11 (best) | 0.73 (k=11) | 0.86 (k=5) |
| similarity-weighted kNN | 0.66 | 0.84 |
| max sim to red minus max sim to non-red | 0.51 | 0.77 |
| same, red vs green only | 0.54 | 0.80 |
| one red centroid vs one non-red centroid | 0.65 | 0.82 |
| **per-category centroids** | **0.81** | **0.90** |
| logistic regression on top-k similarities | 0.65 | 0.83 |
| logistic regression on per-category centroid similarities | 0.64 | 0.84 |
| (every method with the query prefix) | 0.07-0.12 lower, except one | |

**Chosen:** per-category centroids, no prefix. Score = max cosine to one of the 20 red category centroids minus max
cosine to one of the 11 non-red centroids (yellow + 10 green categories); red when score > threshold
(strict 0.0304, wide 0.0080). Fitted on all examples: `model.npz` (31 x 384 float16 = 24 KB), `model.json`.

**Phase C: held-out lists** (`evaluate.py`, `eval_results.json`). Words = `confidence.urgent(text, typos.correct(text))`
as `assistant.is_danger` calls it (its numbers on list 2 match `independent2/RESULTS.md` exactly: 230/249, 85/111,
127/246). List 1 is in-sample for the words now (19c2db2's fixes were built on it); list 2 is held out for both.
Both lists are held out for the meaning check.

## The table

Flagged as urgent, count / total. "Green" = false positives (counterexamples + mild + others).

| | list 1 (690) red | yellow | green | list 2 (606) red | yellow | green |
|---|---|---|---|---|---|---|
| words only (today) | 340/343 (99%) | 98/104 | 76/243 (31%) | **230/249 (92.4%)** | 85/111 (77%) | **127/246 (52%)** |
| meaning only, strict | 253 (74%) | 40 | 35 (14%) | 191 (77%) | 33 | 37 (15%) |
| meaning only, wide | 297 (87%) | 56 | 62 (26%) | 210 (84%) | 53 | 62 (25%) |
| words OR meaning, strict | 340 | 99 | 92 (38%) | **240 (96.4%)** | 87 | **140 (57%)** |
| words OR meaning, wide | 341 | 100 | 106 (44%) | **244 (98.0%)** | 93 (84%) | **147 (60%)** |
| words AND meaning, wide | 296 | 55 | 33 (14%) | 197 (79%) | 45 | 42 (17%) |

AUC of the meaning score, red vs green: 0.88 on both lists.

In-sample triage sets (`cases.py`, `cases128`, `cases154`, `cases241`, `cases_glued`: 273 red, 94 yellow, 148 green):
words 272/273 red (the miss is "snakebitmyleg", which meaning also misses); words OR meaning 272/273 at both settings:
**no red lost**. Green 63 → 63 (strict) / 67 (wide).

### By kind, list 2 (wide), words / meaning / OR

| kind | red | yellow | green |
|---|---|---|---|
| plain | 54 / 46 / 56 of 57 | 36 / 18 / 38 of 42 | |
| fragment | 39 / 34 / 42 of 45 | 7 / 3 / 7 of 15 | 3 / 1 / 3 of 11 |
| slang | 22 / 22 / 26 of 28 | 8 / 4 / 9 of 10 | 15 / 4 / 17 of 26 |
| elderly | 21 / 22 / 24 of 24 | 8 / 5 / 9 of 9 | 1 / 3 / 4 of 6 |
| child | 36 / 31 / 37 of 37 | 16 / 15 / 18 of 19 | 5 / 9 / 9 of 11 |
| mental-health | 3 / 6 / 6 of 6 | 3 / 5 / 5 of 6 | |
| non-native | 16 / 14 / 17 of 17 | 4 / 4 / 5 of 7 | 2 / 0 / 2 of 8 |
| buried | 13 / 11 / 13 of 13 | | |
| counterexample | | | 82 / 36 / 95 of 135 |
| mild | | | 43 / 24 / 50 of 109 |

(Every kind, both lists, both settings: `eval_results.json` → `by_kind`.) Meaning helps most where words are weakest:
mental health (3 → 6 of 6), slang, elderly, everyday wordings.

### Red the words miss and meaning catches (list 2, wide: 14 of 19)

"stoke symptoms my dad", "my mate chainsawed his thigh its pumping", "his throat is closing after peanuts", "my brother
is ODing", "found an old man outside in the snow, barely awake, skin icy", "acid splashed in her eyes at work", "my son
says voices are telling him to jump", "cant do this no more. took everything in the cabinet", "unalive myself tonight how
many", "my mate is having a turn, can't get a word out of him", "something wrong with grandma she just staring and
drooling", "child has croup and making squeaky noise even when calm", "my bp is very high 200 and my vision is going
blurry", "mum's speech went weird for 5 mins then back to normal". (Strict catches 10 of these: not "stoke symptoms", the
"took everything" and "unalive" lines, or the blood pressure one.) List 1: only "911" (wide).

### Red still missed by words OR meaning

- List 2 (wide): "anna flack sis" (voice-to-text), "my missus is having a do and she's grey", "narcan how",
  "compressions how fast", "my poo is black and tarry and i feel a bit lightheaded". Strict adds "stoke symptoms my dad",
  "cant do this no more. took everything in the cabinet", "unalive myself tonight how many", "my bp is very high 200 …".
- List 1: "myboyiscoking", "ma tête tourne et je vois flou soudain" (and "911" at strict).

Meaning alone misses some easy ones the words catch ("cpr", "fentynal", "pinpoint pupils not waking up blue lips",
"is fitting and wont stop been 6 min"): one-word fragments and lists of signs sit far from sentence-shaped centroids.
It is an addition to the words, not a replacement.

### New false positives (meaning flags, words don't)

List 2, wide 28 (strict 15): child/elderly everyday questions pulled toward the baby/child/elderly red centroids
("my toddler wont eat vegetables is that ok", "my kid has a wobbly tooth", "my grandma's feet are always cold", "the
toddler had a meltdown in the supermarket"), idioms the examples didn't cover ("nan's having kittens about the wedding
seating", "he's gonna have a cow", "the company is on life support", "lyrics to stayin alive"), objects in danger
("my phone got water damage, dropped in the pool", "the engine is overheating", "my goldfish is floating upside down"),
and 8 yellows. List 1, wide 32 (strict 17): the same kinds, plus some the words list cuts out and meaning doesn't
("bleed the radiator", "my sourdough starter isnt breathing", "the engine seized", "he collapsed into laughter").
Full lists: `eval_results.json` → `new_fp`. Today a false match only means pages are never held back, so the cost is small.

## Practicality (Phase D, `bench.py`, `bench_results.json`)

This PC (Ryzen 7 5800X3D), CPU, fresh process, model file in the OS cache (a cold first read from disk will be slower):

| | fp32 model (127 MB, as shipped for hybrid) | int8 dynamic-quantized (32 MB) |
|---|---|---|
| import numpy + onnxruntime + tokenizers | 0.26 s | 0.26 s |
| session + tokenizer load | 0.18-0.57 s | 0.13 s |
| memory (RSS) after load | 197 MB (+147 MB over the imports) | 103 MB (+53 MB) |
| per question, median / p95 (2 threads) | 4.3 / 6.8 ms | 2.6 / 4.0 ms |
| per question, 1 thread / 8 threads | 7.6 / 3.0 ms | |

GPU: not relevant (the installed onnxruntime has only the CPU provider, and a question takes a few ms). The int8 model
gives the same results (refitted centroids with it, `eval_results_int8.json`): list 2 OR wide 244/249 red, 147/246 green;
strict 240 and 142. Example vectors to ship: 24 KB (31 centroids, float16); they must be computed with the same model
file that ships.

**What the desktop build has today:** `packaging/build_app_windows.sh` bundles numpy and the onnxruntime and tokenizers
binaries (`--collect-binaries`) and `retrieval` as a hidden import, but not the model: `retrieval.AVAILABLE` is only true
when `DATA/derived/models/bge-small-en-v1.5/model.onnx` exists, setup's manifest has only the LLM, and
`app/tests/test_bridge.py` `WholeProcess.test_no_listening_socket_and_no_model` asserts that no onnx module and no
`bge-small` / `derived/models` file is loaded in the desktop process. So the meaning model exists only in hybrid
(server) mode today.

## Recommendation

1. **Worth adding as "words OR meaning", wide threshold.** On the fresh list it lifts red from 92.4% to 98.0% (14 of 19
   misses), yellow 77% → 84%, for +20 green flags (52% → 60%), and loses nothing on the in-sample sets. Use it only to
   widen `urgent()` (pages never held back), not to narrow it, and not alone: meaning alone is 84%.
2. **Ship:** the int8 bge-small (32 MB) + tokenizer.json (0.7 MB) + the 24 KB centroid file, in the app (not a
   download), with a small `engine/` module that loads them lazily on a background thread when the chat opens (~0.4 s)
   and never blocks: until loaded, or if loading fails, the words alone decide, as today. ~3-5 ms a question, ~55 MB
   memory. Precomputed example vectors alone are not enough: the question must be embedded too.
3. **Before it lands:** the desktop's "no model in the process" test has to change on purpose (the onnxruntime
   telemetry handling of `engine/quiet_onnx.py` then matters in the desktop too); the bge licence (MIT) and the model's
   provenance go in THIRD_PARTY_NOTICES as today for hybrid; and in hybrid mode reuse the loaded `Embedder` (but its
   fp32 model needs its own centroids).
4. **Test again on a third fresh list** before trusting the numbers: the threshold was set on the examples only, but
   list 2's false positives (children, elderly, idioms) show where examples are thin. Adding green examples for them
   now would be tuning on the test list.

## Limitations

- The examples, lists 1 and 2 and the triage sets were all written by the same model family (Claude). The lists were
  never used to build the examples, but shared habits of phrasing (and of what counts as a "look-alike") make the
  held-out numbers optimistic for real people's messages.
- List 2 has 249 red lines: one line is 0.4 points. 14 rescued lines is a real but small sample.
- Load times are with a warm file cache on a fast PC; a slow laptop or cold disk will be slower to load (not per question).
- English only: the French and Spanish lines are missed or caught by chance.

## Files

`make_examples.py` / `examples.jsonl` (phase A), `common.py` (engine imports, cached embeddings), `cv.py` /
`cv_results.json` (phase B), `evaluate.py` / `eval_results.json` / `eval_results_int8.json` / `model*.json` /
`model*.npz` (phase C), `bench.py` / `bench_results.json` (phase D), `words_on_examples.py`. `cache/` holds the
embeddings and the int8 model copy (`cache/int8/`, 32 MB; delete freely).
