# Meaning check on the llama.cpp runner (GGUF q8_0) vs ONNX int8: statistics (2026-11-19)

Measurement only. Nothing committed or written to data folders. Script `llamacpp_stats.py`, all numbers in `LLAMACPP_STATS.json`
(per-line examples, disagreements, misses), refit centroids in `model_gguf.npz`.
Setup: scratch runner `work-meaning\bin-win\lastbook-llm.exe --embed --cpu-only --threads 2`, `bge-small-en-v1.5-q8_0.gguf`,
requests `{"op":"embed","texts":[..],"max_tokens":320}`. Words = `confidence.urgent(q, typos.correct(q))` at 9bd116e.
int8 = branch 51c7a4f (`model_int8.onnx` + its shipped centroids, wide 0.00663 / strict as shipped), reproduced here:
list 1 341/343, list 2 245/249, list 3 186/199 red, as measured before.

## 1. Refit on the examples only (689 examples, 20 red + 11 non-red centroids, 5-fold x 3 by category)

| | GGUF q8_0 | int8 prototype |
|---|---|---|
| strict: out-of-fold red recall at 5% green FP | **80.3%** (green FP 4.8%, yellow flagged 16%) | 81% |
| wide: red recall at 10% green FP | **89.5%** (green FP 10.0%, yellow flagged 28.5%) | 90% |
| thresholds strict / wide | 0.0317 / 0.0084 | 0.0304 / 0.0080 (fp32) |

Same recall within half a point. No test list was used to choose anything.

## 2. Held-out lists (red / yellow / green flagged urgent; green = counterexample + mild)

| list | n red/yel/green | words only | words OR int8 wide | words OR GGUF wide | words OR GGUF strict |
|---|---|---|---|---|---|
| 1 | 343/104/243 | 340 / 98 / 76 | 341 / 101 / 106 | **341 / 100 / 104** | 340 / 99 / 91 |
| 2 | 249/111/246 | 230 / 85 / 127 | 245 / 93 / 147 | **243 / 93 / 147** | 240 / 88 / 140 |
| 3 | 199/78/254 | 173 / 55 / 154 | 186 / 65 / 171 | **188 / 62 / 173** | 182 / 61 / 160 |

(int8 strict for reference: 340/99/95, 241/89/143, 185/61/162.)
Red recall words OR GGUF wide: 99.4% / 97.6% / 94.5% (int8: 99.4 / 98.4 / 93.5). Green split
(counterexample / mild): GGUF wide list 1 39/128 and 65/115, list 2 95/135 and 50/109, list 3 110/147 and 65/110 (int8: 41, 65; 96, 49; 109, 64).

Meaning alone, wide, red/yellow/green: GGUF 297/56/60, 210/53/62, 162/35/75; int8 294/56/62, 212/52/64, 159/39/71.

**Red caught only by meaning (words miss): GGUF wide / int8 wide / GGUF strict**
- list 1: 1 / 1 / 0 ("911")
- list 2: 13 / 15 / 10 (GGUF misses the two int8 gets: "my missus is having a do and she's grey", "my bp is very high 200 and my vision is going blurry")
- list 3: 15 / 13 / 9 (GGUF gets "standing on the bridge" and "ive written the notes and given my cat to my sister", int8 doesn't)

**Green flagged only by meaning (wide GGUF / int8; strict GGUF):** list 1 28 / 30; 15. List 2 20 / 20; 13. List 3 19 / 17; 6.
Yellow only by meaning, GGUF wide: 2 / 8 / 7.

**Red still missed by words OR GGUF wide:** list 1 2 ("myboyiscoking", a French line; same as int8); list 2 6 (int8 4);
list 3 11 (int8 13).

**Disagreements GGUF wide vs int8 wide**, meaning alone / final OR verdict: list 1 31 / 9, list 2 25 / 8, list 3 25 / 11,
triage 27 / 5. They go both ways and sit at scores near the threshold (|score| < 0.02). By label on the meaning-alone
disagreements (GGUF fires, int8 not / int8 fires, GGUF not): list 1 red 8/5, yellow 3/3, green 5/7; list 2 red 4/6,
yellow 4/3, green 3/5; list 3 red 5/2, yellow 1/5, green 8/4. Of these, the ones that change the OR verdict (words silent):
- GGUF only: "my son has nits", "the dog is panting after walk normal?", "grazed my knee falling off skateboard", "the company is on life support",
  "cold feet before the wedding", "new red sore on his bottom from the wheelchair", "back went again lifting plasterboard"
  (all green); "ive written the notes and given my cat to my sister", "standing on the bridge" (red, right).
- int8 only: "had diarrhea twice today drinking ok", "breath of fresh air", "the pipes froze and burst", "hit the wall at mile 20 of the marathon"
  (green); "my missus is having a do and she's grey", "my bp is very high 200..." (red, right), "peeing loads and always thirsty" (yellow).
Examples: `LLAMACPP_STATS.json` -> `disagree_OR_verdict_wide`, `disagree_meaning_gguf_wide_vs_int8_wide`.

## 3. In-sample regression (triage sets, 273 red / 94 yellow / 148 green)

Words 272 / 75 / 63 (the one miss is "snakebitmyleg"). Words OR GGUF wide 272 / 79 / 67; strict 272 / 76 / 63; int8 wide 272 / 78 / 69.
**No red lost with OR** (`red_lost_vs_words_gguf_wide` is empty on every list).

## 4. Speed and memory, through the pipe (2,342 lines incl. the 689 examples; CPU, 2 threads, Ryzen 7 5800X3D)

| | median | p95 | p99 | max |
|---|---|---|---|---|
| runner, one question per request, round trip | **5.2 ms** | 8.9 ms | 12.1 ms | 24.5 ms |
| int8 ONNX in process (every 5th line) | 2.2 ms | 3.7 ms | | |

Batching: 8 per request 5.4 ms/question, 32 per request 5.3, 128 per request 5.3. So batching gives no gain; one question per
request is the right use. Runner memory after the run: 73 MB peak working set, 66 MB private (69 MB current); load 0.2 s.

## Verdict

GGUF q8_0 on the runner is as good as ONNX int8: same CV recall (80.3/89.5 vs 81/90), words OR meaning red 341/243/188 vs 341/245/186 (lists 1/2/3) (+2 on list 3, -2 on list 2, noise), the same green flags (+-2), no red lost in-sample. Costs about 3 ms more per
question and a 66 MB second process, but no onnxruntime. The two backends disagree on 25-31 lines per list near the
threshold, in both directions, so refit centroids on GGUF vectors (do not reuse the int8 ones).
