Index build: use the GPU for the meaning index (CUDA, then DirectML, then CPU), and a tool to measure it

## What changes

`python retrieval.py`, the one-off build of the meaning index, now tries the GPU layers the installed onnxruntime offers,
in this order, and uses the first that starts:

1. **CUDA** (`onnxruntime-gpu`): NVIDIA.
2. **DirectML** (`onnxruntime-directml`): any DirectX 12 GPU on Windows (AMD, Intel, NVIDIA).
3. **CPU**: what every install does today.

A normal install has the plain `onnxruntime` package, which offers only the CPU, so it gets exactly today's session.

The layer is chosen once per run, when it starts. The build still saves one document at a time, so a run that is stopped
halfway keeps what it finished, and the next run (or the running app, which indexes on the CPU every 5 minutes) carries on
with the rest. Documents added later are embedded by the app on the CPU too. So one index can hold vectors from a GPU layer
and from the CPU. For CUDA and DirectML that does not matter: their vectors match the CPU's more closely than float16
storage keeps them (below). A layer that gave different vectors would need the index to record it.

- `embed_layers(offered, want_gpu)` lists the provider lists to try. Each GPU layer keeps the CPU provider behind it for
  anything it cannot run.
- `Embedder(gpu=False)` and `Index(..., gpu=False)` take the choice. Only the `__main__` build passes `gpu=True`. The
  running app (server, queries) still builds its `Embedder` on the CPU, so a user who happens to have a GPU onnxruntime
  does not get a GPU session, or its video memory use, inside the app.
- CUDA: the build first calls `onnxruntime.preload_dlls()` (onnxruntime-gpu 1.21 and later). On Windows the CUDA and
  cuDNN libraries installed as pip `nvidia-*` wheels are not found without it.
- DirectML: its session gets the two options that provider needs (no memory pattern, sequential execution).
- A layer that cannot start prints why (`CUDAExecutionProvider could not start (...); trying the next`) and the next layer
  is tried. When onnxruntime falls back to the CPU by itself (no CUDA device, for example) it does not raise; the build
  prints the provider it got (`embedding with CUDAExecutionProvider`), so that shows too.
- `LASTBOOK_EMBED_DEVICE=cpu` turns the GPU off; `cuda` or `directml` keeps that one layer (and the CPU if it fails).
- No new dependency. The two GPU packages are optional installs in place of `onnxruntime`. They both install the
  `onnxruntime` module, so one environment has one of them, and that one offers its own layer.
- New `tools/embed_bench.py`, to measure the layers on any computer (below).

`retrieval.py` +41 / -7, `app/tests/test_retrieval.py` +96 / -1, `tools/embed_bench.py` +211,
`app/tests/test_embed_bench.py` +47.

Twelve new tests, which need no GPU and no model. Nine for the layers: layer order with different sets of offered
providers, the environment choice, `Embedder` taking the first layer, `preload_dlls` called for CUDA only (and the
running app printing nothing), the DirectML session options, falling through a failing layer to the next and down to the
CPU, and a failing CPU session still raising. Three for the benchmark's check that nothing is writing to the index.

## Why

On the Medium pack (338,910 passages) the build on the CPU takes about 4.5 hours. Almost all of that is the model step.
With a GPU it drops to about an hour, and this is the smallest change that lets people use one.

## Evidence

**CUDA, timed full build.** The same indexer with onnxruntime-gpu 1.32 and CUDA was compared with the CPU build in
`tools/search_eval/baseline-files.md`:

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

**All three layers, `tools/embed_bench.py` on this branch.** 2,000 passages spread through the Medium pack's index,
batch 48. Windows 10, Ryzen 7 5800X3D (16 logical cores), RTX 3080 Ti. Each row is a separate run with that onnxruntime
package installed:

| Layer | Package | Passages/s | Model step, whole index (est.) | Lowest cosine vs CPU | Nearest same | 10 nearest overlap |
|---|---|---|---|---|---|---|
| cpu | onnxruntime 1.32.0 | 21.8 | 259 min | (reference) | | |
| cuda | onnxruntime-gpu 1.32.0 | 712 | 7.9 min | 1.000000 | 99.2 % | 99.9 % |
| directml | onnxruntime-directml 1.24.4 | 281 | 20 min | 1.000000 | 99.5 % | 100.0 % |

- DirectML uses the same fp32 model as the CPU. Its largest absolute difference from the CPU vectors was 3.3e-7 (on a
  separate run of 3,000 passages), which is float32 rounding, smaller than CUDA's. No vector was bit-identical to the
  CPU one, so it did run on the GPU. "Nearest same" below 100 % comes from near-duplicate passages whose scores tie.
- DirectML on a larger batch: 242 passages/s at 16, 320 at 48, 356 at 128 (3,000 passages).
- The tool's estimates are rough. Against the timed builds above, on this same computer:

  | | Tool's estimate | Timed build |
  |---|---|---|
  | Rest of the build | 68.5 min | 54.5 to 55.4 min |
  | Model step, CPU | 262 min | 217 min |
  | Model step, CUDA | 7.5 min | 11.0 min |
  | Whole build, CPU | 330 min | 273 min |
  | Whole build, CUDA | 76 min | 65 min |

  So they are off by up to a third, in both directions. I could find reasons for each (how the sample is spread over
  documents, the build's batches being cut at document ends, other load on the PC), but one computer cannot tell which
  correction is right on another, so the tool does not try. Timed builds from other computers next to the tool's output
  are what would make the estimates trustworthy.
- With DirectML the whole build would be about 1 h 15 min, by the same rough estimate. I have not timed a full DirectML
  build or compared its index on the 3,258 questions, as I did for CUDA. With vectors this close I do not expect a
  difference.
- The DirectML numbers are from an NVIDIA card. DirectML is there for AMD and Intel cards, and I have not run it on one;
  see the next section.

**Fallbacks, real onnxruntime.** With `CUDA_VISIBLE_DEVICES=-1` (no GPU visible), onnxruntime-gpu fell back to the CPU
and the build printed `embedding with CPUExecutionProvider`. CUDA started with nothing outside the repository loading its
libraries (onnxruntime-gpu 1.32, CUDA 13 and cuDNN 9 pip wheels).

Tests: `python -B -m unittest app.tests.test_retrieval` and the other test modules that import `retrieval` pass, with
`PYTHONUTF8=1` and `PYTHONUTF8=0`.

## Measure it on your computer

The numbers above come from one computer. Results from others would show whether the layers hold up, especially
DirectML on AMD and Intel cards, and CUDA on Linux. With a data folder that already has the meaning index
(`derived/index/semantic.sqlite`; packs do not ship it, Lastbook builds it after the first start, or `python retrieval.py`
does):

```
python -m pip install onnxruntime-directml      # or onnxruntime-gpu[cuda,cudnn] for NVIDIA; one of them, in place of onnxruntime
python tools/embed_bench.py --gpu "your card"   # --data FOLDER if it is not the app's; --n, --docs, --batch, --json out.json
```

A separate environment (a venv, or `pip install --target` and `PYTHONPATH`) keeps the app's own onnxruntime as it is.
The tool embeds `--n` passages (default 2,000) on the CPU and then on each GPU layer that package offers, with the same
`Embedder` the build uses. It also reads `--docs` documents (default 300) with the build's own reading code and writes
them to a temporary folder, to estimate the rest of the build, and prints a rough whole-build estimate for each layer. It
prints a table like the one above, with your operating system, CPU, package and card. A run takes 3 to 5 minutes.

Nothing is written to the data folder. The index is read as immutable, so SQLite does not touch its `-wal` and `-shm`
files either. Because of that, the tool first checks that no build and no running Lastbook is writing to the index, and
stops if one is, so close Lastbook before you run it. The output holds no paths.

The most useful report is this tool's output together with a timed build on the same computer:
`python retrieval.py`, with `LASTBOOK_DATA` set to a copy of the data folder from which `derived/index` is removed, and
its start and end times.

**Help wanted: a Mac.** Nobody has measured any of this on a Mac yet, and I do not have one. On a Mac the tool measures
only the CPU layer today, and that is still useful: CPU numbers and a timed build show how long Mac users wait now.
Beyond that, the next step (below) needs someone with an Apple Silicon Mac who can run the runner's Metal build, once
#407's `--embed` mode is in. The same goes for an AMD or Intel card on Linux.

## What it does not do

- No GPU on a Mac or on Linux with an AMD or Intel card: those get the CPU path as before. DirectML is Windows only. See
  the next section.
- The GPU packages are optional installs and are not in any requirements file, and nothing here installs them. CUDA and
  cuDNN installed some other way than the pip wheels (a system CUDA toolkit) are found the usual way, through the
  search path; I tested only the pip wheels.
- It does not change the vectors the app ships, the index format, or the running app.
- It does not make the rest of the build (3,267 s above) faster.

## Next step: the runner's GPU for Linux and Mac, not in this PR

DirectML covers AMD and Intel cards on Windows. For Linux and Mac the route is the runner (`lastbook-llm`), which gets
an `--embed` mode in #407. It is built with Vulkan on Linux and Windows and with Metal on a Mac
(`packaging/llm/build_llm_*.sh`), and it runs bge-small as a q8_0 GGUF, so the same build could use an AMD, Intel or
NVIDIA GPU on Linux, or a Mac's GPU, with no onnxruntime at all. I measured whether it can replace onnxruntime for the
build, on 3,000 passages spaced evenly through the Medium pack's index (every 112th), one CPU core left free, an NVIDIA
RTX 3080 Ti on Windows. That is Vulkan on an NVIDIA card, so it shows the route works, not how fast an AMD or Intel card
is; Metal is not measured at all:

| Way of making the vectors | Passages per second |
|---|---|
| onnxruntime CPU (8 threads, fp32) | 20 |
| runner `--embed` CPU (8 threads, q8_0) | 25 to 26 |
| runner `--embed` CPU (15 threads, q8_0) | 32 |
| runner `--embed` Vulkan (q8_0, 64 texts a request) | 188 |
| onnxruntime DirectML (fp32, batches of 48) | 320 |
| onnxruntime CUDA (fp32 weights, batches of 48) | 629 |

Agreement with the onnxruntime CPU vectors of the same passages (cosine):

| | lowest | 1st percentile | median |
|---|---|---|---|
| onnxruntime CUDA | 1.000000 | 1.000000 | 1.000000 |
| onnxruntime DirectML | 1.000000 | 1.000000 | 1.000000 |
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

The plan: this PR first. The runner layer waits until someone can run it on the hardware it is for: an AMD or Intel card
on Linux, or a Mac. I have neither, and testing it on my NVIDIA card proves little, since NVIDIA gets CUDA first. When
it comes, it would be opt-in at first (`LASTBOOK_EMBED_DEVICE=runner`, never chosen on its own) until those reports are
in, with the full-index comparison above and the index recording which model built it. The runner is not an onnxruntime
provider, so it needs its own client class with the same `embed()`, tried in `Embedder`'s layer loop after DirectML;
the layers in this PR stay as they are.

STAirye

🤖 Generated with [Claude Code](https://claude.com/claude-code)
