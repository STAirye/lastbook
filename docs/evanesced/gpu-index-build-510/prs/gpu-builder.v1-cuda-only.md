Index build: use the GPU (CUDA) for the meaning index when onnxruntime offers it

## What changes

`python retrieval.py`, the one-off build of the meaning index, now asks onnxruntime for `CUDAExecutionProvider` first when
the installed onnxruntime offers it, and keeps `CPUExecutionProvider` behind it. Otherwise nothing changes: a normal
CPU-only install gets exactly today's session. `retrieval.py` +26 / -5, `app/tests/test_retrieval.py` +65 / -1.

- `embed_providers(offered, want_gpu)` picks the providers. The GPU is used only when the build asks for it, the
  installed onnxruntime lists CUDA, and `LASTBOOK_EMBED_DEVICE` is not `cpu`.
- `Embedder(gpu=False)` and `Index(..., gpu=False)` take the choice. Only the `__main__` build passes `gpu=True`. The
  running app (server, queries) still builds its `Embedder` on the CPU, so a user who happens to have onnxruntime-gpu does
  not get a GPU session, or its video memory use, inside the app.
- When CUDA is chosen, the build first calls `onnxruntime.preload_dlls()` (onnxruntime-gpu 1.21 and later). On Windows
  the CUDA and cuDNN libraries installed as pip `nvidia-*` wheels are not found without it.
- If the GPU session cannot be created, the build prints why (`GPU session could not start (...); building on the CPU`)
  and carries on with the CPU provider. When onnxruntime falls back by itself (no CUDA device, for example) it does not
  raise, and the next line shows it.
- The build prints which provider it got (`embedding with CUDAExecutionProvider`), so a fallback to the CPU is visible.
- `LASTBOOK_EMBED_DEVICE=cpu` turns it off.
- No new dependency. `onnxruntime-gpu` (with its CUDA and cuDNN libraries) is an optional install in place of `onnxruntime`.

Five new tests, which need no GPU and no model: provider choice with a list of offered providers, the environment opt-out,
`Embedder` handing the choice to a stubbed onnxruntime session, `preload_dlls` called for the GPU only (and the running
app printing nothing), and the fallback to the CPU when the stubbed GPU session raises.

## Why

On the Medium pack (338,910 passages) the build on the CPU takes about 4.5 hours. Almost all of that is the model step. A
person who has an NVIDIA card can cut it to about an hour, and this is the smallest change that lets them.

## Evidence

The same indexer with onnxruntime-gpu 1.32 and CUDA was compared with the CPU build in `tools/search_eval/baseline-files.md`:

- Same `text_sha256`: the same passages, in the same order, are embedded.
- Lowest cosine between the CPU and GPU vector of a passage: 0.999998. Largest absolute difference 0.00049, which is
  float16 rounding of the stored vectors.
- Hybrid results on 3,258 questions: 0 yes/no changes, 66 near-tied page-order swaps.
- Timed builds on an idle PC (8 threads):

  | Build | Total | Of which model | Everything else |
  |---|---|---|---|
  | CPU | 4 h 33 min (16,353 s) | 13,029 s | 3,325 s |
  | GPU | 1 h 05 min (3,928 s) | 662 s | 3,267 s |

  The model step is 19.7 times faster, the whole build 4.2 times. The rest (reading, cutting into passages, writing the
  database) is unchanged, which is why the build does not get faster than about an hour.

Smoke test of this branch with the real model (onnxruntime-gpu 1.32, CUDA 13 and cuDNN 9 pip wheels, Windows), on 480
passages from the Medium pack's index, with nothing outside the repository loading the CUDA libraries: the `Embedder`
chose CUDA (printed), 715 passages/s; with `LASTBOOK_EMBED_DEVICE=cpu` it chose the CPU provider and gave 26 passages/s;
lowest cosine between the two 0.99999976, largest absolute difference 0.0001. With `CUDA_VISIBLE_DEVICES=-1` (no GPU
visible) onnxruntime fell back to the CPU, the build printed `embedding with CPUExecutionProvider`, and embedding worked.

Tests: `python -B -m unittest app.tests.test_retrieval` and the other test modules that import `retrieval` pass, with
`PYTHONUTF8=1` and `PYTHONUTF8=0`.

## What it does not do

- NVIDIA only (CUDA). An AMD or Intel GPU, or a Mac, gets the CPU path as before. See the next section.
- onnxruntime-gpu is an optional install and is not in any requirements file, and nothing here installs it. CUDA and
  cuDNN installed some other way than the pip wheels (a system CUDA toolkit) are found the usual way, through the
  search path; I tested only the pip wheels.
- It does not change the vectors the app ships, the index format, or the running app.
- It does not make the rest of the build (3,267 s above) faster.

## Next step: any GPU through the runner (Vulkan), not in this PR

The runner (`lastbook-llm`, built with Vulkan) gets an `--embed` mode in #407. It runs bge-small as a q8_0 GGUF, so the
same build could run on an AMD, Intel or NVIDIA GPU, and on a Mac, with no onnxruntime at all. I measured whether it can
replace onnxruntime for the build, on 3,000 passages spaced evenly through the Medium pack's index (every 112th), one CPU
core left free, an NVIDIA RTX 3080 Ti (Vulkan used here for the NVIDIA card, so this shows the route works, not how fast an
AMD or Intel card is):

| Way of making the vectors | Passages per second |
|---|---|
| onnxruntime CPU (8 threads, fp32) | 20 |
| runner `--embed` CPU (8 threads, q8_0) | 25 to 26 |
| runner `--embed` CPU (15 threads, q8_0) | 32 |
| runner `--embed` Vulkan (q8_0, 64 texts a request) | 188 |
| onnxruntime CUDA (fp32 weights, batches of 48) | 629 |

Agreement with the onnxruntime CPU vectors of the same passages (cosine):

| | lowest | 1st percentile | median |
|---|---|---|---|
| onnxruntime CUDA | 1.000000 | 1.000000 | 1.000000 |
| runner Vulkan | 0.999868 | 0.999911 | 0.999936 |
| runner CPU | 0.999734 | 0.999804 | 0.999868 |

None is below 0.999. Inside the 3,000 passages, each passage's 10 nearest others by the runner Vulkan vectors overlap the
CPU ones by 98.7 % (the nearest one is the same for 97.5 %). On 400 passages the runner's token count was the same as the
`tokenizers` count (bge's own tokenizer.json) for every passage, 4 of them cut at 320 tokens.

What this says:

- Vector agreement is not the problem: q8_0 costs about 0.0001 to 0.0003 of cosine, which is more than float16 rounding
  (0.0005 absolute) but small next to the gaps between ranked passages. It has not been checked on the 3,258 questions the
  way the CUDA build was, so I would not call it the same index until it is.
- Tokenizer differences did not show on 400 passages. A larger check (all 3,000, and the passages with unusual characters) is
  still to do.
- Speed: 188 passages/s would make the model step about 30 minutes for the Medium pack (338,910 / 188), against 3.6 hours on
  the CPU and 11 minutes with CUDA; with the unchanged 55 minutes for everything else, the build would be about 1 h 25 min
  against 1 h 05 min with CUDA. This is an estimate from the 3,000 passages, not a timed build, and the runner is not tuned
  (one request at a time, 64 texts). Larger batches or several requests may be faster.
- What would block it: (1) the index would hold q8_0 vectors, so the index version or a note must say so, and a full-index
  comparison on the 3,258 questions must show no yes/no changes; (2) the runner's `ready` message in #407 has to be what the
  Python side checks (the build I measured with did not yet report pooling and dimension); (3) a Python class that talks to
  the runner, restarts it if it stops, and falls back to onnxruntime when the runner has no GPU, as `tools/meaning_red_model.py`
  already does for part 7; (4) the same runner binary must be present when someone builds an index, which it is in a
  release but not in a source checkout.

The plan: this PR first (small, and the evidence exists). Then, once #407 is merged, a second PR that adds the runner as
another choice for `LASTBOOK_EMBED_DEVICE`, with the full-index comparison above. Nothing in this PR has to change for that.

STAirye

🤖 Generated with [Claude Code](https://claude.com/claude-code)
