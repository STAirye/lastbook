# Smoke test: the meaning check on the app's llama.cpp runner (2026-11-19)

Question: can `engine/meaning_red.py` (bge-small-en-v1.5, [CLS], 31 centroids) run on lastbook-llm instead of
onnxruntime? **Yes. No blocker found.** Smoke test only: 40 sentences + 11 edge cases, no statistics.

Files (scratch, not in git): `gguf/` here — `bge-small-en-v1.5-{f32,f16,q8_0}.gguf`, `probe.cpp`/`probe.exe`,
`compare.py` (+ `compare_results.json`), `runner_test.py`. Scratch build: `D:\buildtools\lastbook-llm\work-meaning\`
(its own llama.cpp clone at b12032, cloned locally from `work\llama.cpp`). Nothing written to `derived/llm/bin-win` or
`D:\LastbookData`.

## 1. GGUF conversion

`work\llama.cpp\convert_hf_to_gguf.py` (b12032, `dde879bc`) with its own `gguf-py` on `PYTHONPATH`, from
`D:\LastbookData\derived\models\bge-small-en-v1.5-hf\`. Works with what is installed (torch, transformers, numpy; no
sentencepiece needed). About 5 s each.

| type | size | metadata |
|---|---|---|
| f32 | 133 MB | `bert`, 12 blocks, 384 dims, ctx 512, `bert.pooling_type = 2` (CLS, read from 1_Pooling), tokenizer `bert` (WordPiece) |
| f16 | 68 MB | same |
| q8_0 | 37 MB | same (ONNX int8 today: 34 MB) |

Load warning, harmless: `special_eos_id is not in special_eog_ids`.

## 2. Embeddings with the runner

**a. Unchanged `bin-win\libllama.dll`:** a 70-line test program (`gguf/probe.cpp`, built with the script's llvm-mingw
clang++ against `work\build-win`'s import libraries, which are the same build as `bin-win`: SHA-256 checked) loads the
GGUF with `embeddings = true`, `pooling_type = CLS`, `llama_encode`, `llama_get_embeddings_seq`. It works, CPU and Vulkan.
So the shipped llama.cpp DLLs already embed BERT. Only the runner program needs a change.

**b. Runner change:** there is already an uncommitted (staged) diff for this in the worktree
`.claude/worktrees/runner-embed` (branch `fork/runner-embed`, from an earlier session, 2026-11-17; base
`lastbook_llm.cpp` identical to the fork's current one). I used it unchanged. `packaging/llm/lastbook_llm.cpp`
**+88 / -9 lines**:
- `--embed`: `cp.embeddings = true`, `pooling_type = CLS`, `n_ctx = n_batch = n_ubatch = 512` by default.
- new request `{"op":"embed","id":..,"texts":[..],"max_tokens":320}` → `{"ev":"embedding","vectors":[[..]],"n_tokens":[..],"ms":..}`;
  tokenizes with the model's [CLS]/[SEP], cuts at `min(max_tokens, n_ubatch)` keeping [SEP] last, `llama_encode`, unit vector.
- `gen` is refused in embed mode and `embed` in chat mode (`unknown op`).

Built with the unchanged `build_llm_windows.sh` (`TOOLS=D:\buildtools\lastbook-llm W=D:\buildtools\lastbook-llm\work-meaning`):
full build ~2 min (64 s, then a compiler step failed with no message — `ggml-cpu-cannonlake` `traits.cpp` — rerun
resumed and finished in 59 s; looks transient). Rebuild after touching only `lastbook_llm.cpp`: 16 s. The script's own
checks (no network imports, no local folders inside) passed. `lastbook-llm.exe` 344 KB (was 336 KB).

## 3. Results

### Agreement (40 sentences: 20 random from `examples.jsonl`, seed 7; 20 invented, with typos)

Centroids and threshold of the integrated check (`centroids.npz`, fit on **int8** embeddings, wide 0.0066).

| | cos vs ONNX fp32 min / mean | cos vs ONNX int8 min / mean | red verdicts (of 40) | disagreements |
|---|---|---|---|---|
| GGUF f32 (CPU / Vulkan) | 1.00000 / 1.00000 | 0.964 / 0.982 | 24 | 0 vs fp32, 1 vs int8 |
| GGUF f16 | 1.00000 / 1.00000 | 0.964 / 0.982 | 24 | 0 vs fp32, 1 vs int8 |
| GGUF q8_0 (probe and runner) | 0.99981 / 0.99984 | 0.964 / 0.982 | 24 | 0 vs fp32, 1 vs int8 |
| ONNX int8 (today) vs fp32 | 0.964 / 0.982 | — | 23 | — |

- The GGUF files, q8_0 included, match **fp32 ONNX**, and much more closely than the int8 ONNX does. Token counts
  matched the HF tokenizer on all 40 sentences and all edge cases.
- The one disagreement is with the int8 path: "grandpa face drooping and slurred speach" is red for GGUF and fp32 and not
  red for int8 (with the int8 centroids). That's an int8 quirk, not a GGUF one.
- With the fp32 centroids (`model.npz`, wide 0.00797), GGUF q8_0 vs ONNX fp32: 0 disagreements, 24 = 24 red, largest
  score difference 0.0026.
- **So a switch needs centroids and thresholds refit on GGUF (or fp32) vectors** (the fp32 ones in `model.npz` would do),
  not the int8 ones shipped in the branch.

### Speed and memory (Ryzen 7 5800X3D, 2 threads)

| | load | per sentence | memory (peak working set / private) |
|---|---|---|---|
| runner `--embed --cpu-only`, q8_0 | 0.23 s spawn to ready | 6.5 ms round trip through the pipe (median; max 11); about 4.3 ms of compute | 62–71 MB / 65–68 MB |
| probe CPU f16 / f32 | 0.14 s | 5.3 / 4.6 ms | 80 / 121 MB |
| runner Vulkan q8_0 | 0.28 s | 7.3 ms median, **first sentences up to ~1 s** | 156 MB, +55 MB VRAM |
| probe Vulkan f16 | 0.2 s | 12 ms median, **one sentence took 10.6 s** (shader pipelines built per new size) | |
| batch of 40 in one request (CPU) | | 268 ms total | |

Use `--cpu-only`. Vulkan is slower per question and has multi-second first-time stalls. For comparison, today's int8 ONNX:
2.6 ms per question (RESULTS.md), in process.

### Crash cases (runner, q8_0, CPU): none

Empty string, a lone space, a zero-width space → 2 tokens ([CLS][SEP]), a vector, no crash (the app already skips empty
text). 700 words with `max_tokens` 320 → 320; with `max_tokens` 5000 → capped at 512, no crash. Emoji, Spanish, Chinese,
Russian, embedded newlines, `%s {} " \` → fine, cos ≥ 0.9994 with fp32. Bad requests: `texts` not strings → `error
bad_request`; no `texts` → empty `vectors`; `gen` in embed mode → `error unknown op`. The process stays alive after each.
Nit: `max_tokens` ≤ 0 clamps to 2, so the text is silently dropped; it should fall back to the default.
Nit: the embed runner's ready event says `"swa_check": true`, which means nothing there.

### Beside Gemma

The app's own runner (`derived/llm/bin-win`, unchanged) loaded `gemma-4-E4B-it-Q4_K_M.gguf` (ready in 18 s, ctx 16384,
VRAM 665 → 3854 MiB, 3.6 GB working set) while the embed runner (CPU) stayed resident. Embeddings beside it: 7.0 ms
median. An 8-token Gemma request ended `eog`. Both processes alive. Only one short request, no long chat.

## 4. Mac / Linux (read only)

- `build_llm_linux.sh`: the same layout as Windows (gcc, shared libs, Vulkan + every CPU variant, `$ORIGIN` rpath),
  and it compiles the same `lastbook_llm.cpp`. The change builds there with no script edit. Not tested.
- `build_llm_macos.sh`: static libllama + Metal/BLAS, also compiles the same `lastbook_llm.cpp`. No script edit
  expected. BERT on Metal is upstream-supported, but `--cpu-only` (Accelerate) keeps it like Windows. Not tested
  (no Mac here).
- The GGUF file is the same on every platform: one 37 MB q8_0 for all three, plus the centroids.

## What a switch would take

1. Runner: the 88/9-line diff above (it exists, uncommitted, in `.claude/worktrees/runner-embed`), plus the
   `max_tokens` ≤ 0 nit. Rebuild the runner on all three platforms. The libllama/ggml DLLs don't change.
2. Python: in `meaning_red.Model`, instead of onnxruntime + tokenizers, spawn `lastbook-llm --model bge-small-q8_0.gguf
   --embed --cpu-only --threads 2`, wait for `ready`, then one `embed` line per question (about 6.5 ms). That's a second
   long-lived runner process beside the chat one: about 65 MB RAM and no VRAM. The runner tokenizes itself (no
   tokenizer.json), so the manifest becomes the GGUF + centroids.
3. Refit centroids/thresholds on GGUF vectors (`make_examples`/`evaluate` with the GGUF embedder; fp32 `model.npz`
   already agrees on this sample).
4. The win: this check no longer needs onnxruntime and its telemetry silencing. Hybrid search's `retrieval.Embedder`
   still uses onnxruntime unless it moves too: the same `--embed` mode would serve it, since it's the same model with
   `MAX_TOKENS` 320. The cost: one more process to manage, and ~4 ms more per question than in-process int8.
