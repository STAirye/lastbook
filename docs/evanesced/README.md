# docs/evanesced/ (fork only)

The **intermediate work** of fork branches and worktrees whose work is finished: the repro scripts, measuring
harnesses and notes behind the changes recorded in [FORK.md](../FORK.md). Nothing here is imported, packaged, shipped or
run by the tests. It is **documentation of why**: the branch, worktree or session where it lived goes away, and a cold
session has no other source.

The name: the branch evanesces, its scripts don't.

This folder is fork-only, like `FORK.md`: strip it from anything proposed upstream.

## Rules

1. **When.** Working scripts live in `.claude/drafts/` (untracked) or a session's scratchpad (temporary) while the work
   is open. When the branch, worktree or session that made them finishes its work (merged, dropped, or the PR closed),
   they are archived here, in the same commit as its FORK.md entry or right after.
2. **One folder per batch**, named for what it produced and its FORK.md section (`encyclopedias-3n/`), not by date or
   session.
3. **As they were.** Scripts are copied unchanged, not cleaned up or fixed: a script fixed afterwards no longer proves
   what it proved. A bug, a stale path or a surprise is noted in this README, not corrected in the file.
   **One exception, because this fork is public:** personal paths (a user folder, a session's scratchpad) are replaced
   with a placeholder such as `<scratchpad>`, and the change is noted here. No names, e-mail addresses, home addresses
   or tokens, ever.
4. **Each batch gets its section below**: what each script did, what it found, where its numbers went (the FORK.md
   section), and its traps (absolute paths, other drafts it imports). A script with no section is an orphan nobody will
   run again.
5. **Never deleted**, not even "cleaning up". Before moving or deleting anything here, check who cites it:
   `git grep -n "<name>"`.

## What does NOT go in

| What | Why | How to get it back |
|---|---|---|
| Copies of the repo's own source files | a stale copy inside `docs/` reads as if it were current | `git show <commit>:<path>` |
| Models, indexes, caches, other binaries (`.gguf`, `.npy`, `.npz`, `.onnx`, `cache/`) | large, regenerable, and they don't explain anything | the archived script that built them; where they live on the PC is noted in the batch's section |
| Big regenerable dumps (full search logs, merge-tree output) | they weigh more than the command that made them | the command, noted in the section |
| Live-test logs and anything with personal data | the fork is public | not archived |

Short outputs (`.json` of a benchmark's rows, a `.log` of a build) do go in, when the FORK.md numbers come from them.

## Batches

### `encyclopedias-3n/` (FORK.md §3n, 2026-11-19 to 2026-11-21)

Encyclopedia articles back in Chat's first results: whether they need the long-page sections, the best-section picker
(`engine/wiki_pick.py`), the urgent label first, the parallel search, the merge that was tried and dropped (the two
searches are now shown apart), and the vector-index prototype (dev toggle, not pursued).

Traps: every script puts `D:\git\lastbook` and `D:\git\lastbook\.claude\drafts\triage` on `sys.path` (the second for
the test questions' `cases.py`, now archived at `triage-search-3k-3m/triage/cases.py`; put it back at that drafts path to run these), and reads
the library from `D:\LastbookData\library-data`. They ran against the fork as it was then: `e2e.py` calls
`assistant.merge_first`, which no longer exists, and `merge_chat.py` measured the merge inside `assistant.chat`, which
no longer merges (both changed in add0b9b).

| Script | What it did | Output |
|---|---|---|
| `measure.py` | article length and where the question's useful words sit (first 2,000 characters or later) | `measure.json` |
| `compare.py` | upstream's first encyclopedia results (raw question, first 2,000 characters) against `wiki_pick` (best section): the 36% → 58% table | `compare.json` |
| `floor.py` | each picked article's score against whether it is useful (a minimum score was tried and dropped), and the library search's time | `floor.json` |
| `e2e.py` | end to end on the real library, keyword-only: urgent label, encyclopedias in parallel, the merge (806 → 433 ms) | `e2e.json` |
| `label.py`, `label2.py` | the broad urgent label (`is_danger`) against the precise one (danger signs or meaning) on the test colours | printed |
| `merge_chat.py` | through `assistant.chat` with the model stood in for: where articles landed among library pages (76 of 108 above useful pages by raw score; 10 with the strict rule) | `merge_chat.json`, `merge_chat2.txt`, `merge_chat3.txt` |
| `embed_timing.py`, `embed_timing2.py` | ranking candidates by meaning through the `--embed` runner: 60–200 ms per excerpt, dropped | printed |
| `vectors_app.py` | the app's `first_wiki` with `LASTBOOK_WIKI_VECTORS=1` against 0 on the 253 questions: the everyday 85 → 98, urgent 61 → 92, 583 → 76 ms table | printed |
| `vectors_prefix.py` | `wiki_vectors` with and without bge's query instruction | printed |

`vectors/` is the prototype session's own work (it ran in a separate worktree, since removed):

| File | What it is |
|---|---|
| `RESULTS.md` | the prototype's write-up: counts, build times, sizes, runner-vs-GPU check, benchmark |
| `build.py` | walk each ZIM, cut sections, embed on the GPU (torch, fp16), write the index; times a CPU sample. **Changed on archiving:** the default `BGE_DIR` was a personal scratchpad path, now `<scratchpad>\bge` (set `BGE_DIR` to a local copy of BAAI/bge-small-en-v1.5) |
| `bench.py`, `bench.json` | MDWiki only: runner-vs-GPU vectors, query timing, keyword / vector / hybrid benchmark |
| `bench_all.py`, `bench_all.json` | the same over all three files |
| `build_full.log`, `build_wikibooks.log` | the GPU build logs |

The built indexes are not here (488 MB): on the fork's development PC they are in
`D:\LastbookData\derived\index\vec-*` (f16, int8, `rows.npz` and the converted `rows.json`, `meta.json` per file);
`build.py` and `tools/wiki_vectors_rows.py` rebuild them. The CPU-only build time in RESULTS.md (2.9 h for MDWiki, so
about 6 h for the three) was measured with torch on all cores in batches; the runner, one text at a time, would take
several times longer.

### `triage-search-3k-3m/` (FORK.md §3k–3m, 2026-11-17 to 2026-11-22)

The triage-based search engine: the 362-question test set and its scorer, the long-page sections, typo correction and
glued words, conversations, search confidence, body signs, the four held-out lists, the meaning-based red check, and the
staging of all of it as upstream issue Immortal-Protocols/lastbook#401 and PRs #402–#409 (PR 1 #402 holds the test set
and scorer as `tools/search_eval/` and the methods as `docs/TRIAGE-SEARCH.md`, on branch `triage/1-search-eval`; the
lists there may be reformatted copies of the ones here). Posted 2026-11-22; the PR texts are public. The subfolders
keep the drafts' own folder names (`triage/`, `independent/` … `prs/`); `root/` holds what sat at the top of the drafts.
The Linux build is its own batch, `linux-build-3m/`, below.

**What is not here** (rule: big regenerable dumps, models, caches, binaries):
- Every per-question run dump over 400 KB (`runs/*.json`, `triage/results_*.json`, `triage/conf_*.json`,
  `triage/rab/ab_*.json`, `triage/body/*.json`, `triage/r154/*.json`, `prs/eval*/{kw,hy}-*.json`, `snap-*.json`), about
  150 MB. The `.log`, `report.txt`, scored `results.json` and `.md` files beside them are kept, and the FORK.md numbers
  come from those. To regenerate a dump, run the folder's `*_eval.py` / `run*.py` as its docstring says
  (`set LASTBOOK_CODE=<checkout>`, `set LASTBOOK_DATA=D:\LastbookData-fork-test`, `TH_KW=1` for keyword-only) on the
  commit the RESULTS file names; `score.py` needs a test server for HTTP runs. `triage/RESULTS_154.json` equals
  `triage/r154/analysis.json` (made by `analyze154.py`).
- `meaning/`: the GGUF files (f32 / f16 / q8_0; the shipped q8_0 is in `D:\LastbookData\derived\models\meaning-red\` and
  published as `STAirye/lastbook-meaning-red` on Hugging Face), `cache/` (ONNX int8 model, tokenizer, embedding `.npy`),
  `model*.npz` (centroids; rebuilt by `evaluate.py`), `gguf/probe.exe`. The originals stay in the untracked
  `.claude/drafts/meaning/` on the fork's development PC.
- `prs/rendered/` (duplicates of the texts) and `prs/eval/sections/*.sqlite` (74 MB sections index, built by
  `prs/eval/build_sections.py`).
- `live-test*.log` (personal data), `TODO.md`, the emergency-numbers drafts and `pr-395-reply-*` (other work), and the
  drafts' `__pycache__`.

**Traps.**
- Absolute paths everywhere: `D:\git\lastbook`, `D:\git\lastbook\.claude\drafts\triage` (put on `sys.path` by
  `conf_everyday.py`, `patch_guard_check.py`, `turnhits_eval.py` and others, for `cases.py`, `convos.py`, `score.py`:
  they now live in `triage-search-3k-3m/triage/`), `D:\LastbookData` and `D:\LastbookData-fork-test` (a test copy of the
  library, read only). These are kept as they were.
- Scripts that import another folder: `independent2/analyze2.py` and `independent3/analyze3.py` import
  `heldout-fixes/compare.py`; `independent2/eval2.py` and later are copies of `heldout-fixes/heldout_eval.py` (their
  docstrings still say `indep_eval.py`); `contractions/firsts.py` does `sys.path.insert(0, 'independent2')` and expects to
  run from the drafts root; `triage/mt_oldfork.py` imports `multiturn.py`; the encyclopedias batch imports `cases.py`.
  Several docstrings and `independent4/recover.py` say `.claude/drafts/<folder>/`: that is now
  `docs/evanesced/triage-search-3k-3m/<folder>/`.
- They tested code that was a worktree then and is gone: `.claude/worktrees/{search-before, phrase-injury,
  search-confidence, everyday-buttons, heldout-fixes, meaning-check}` (and the body-signs and glued-words branches the
  RESULTS files name), and commits named in the RESULTS files (256d52f, 4ea2d9f, 9712522, 19c2db2, 51c7a4f, c7795b5).
  Check out the commit, not the branch name; branches `triage/1..8` on STAirye/lastbook are the clean versions.
- They call functions of those commits (`assistant.turn_hits`, `assistant.is_danger`, `engine.typos`, `engine.confidence`,
  `engine.meaning_red`, `server.PHRASES`, `retrieval.AVAILABLE`) that moved or changed later; `meaning/*` also needs
  onnxruntime and a `lastbook-llm.exe` from a scratch `work-meaning` build that is not kept.
- `prs/post.py` pushes branches and opens issues and PRs on GitHub (a run without `--go` is a dry run that writes
  `rendered/`). The issue and PRs are already posted (`post_state.json`: issue 401, PRs 402–409). Do not run it again. It
  also calls `.claude/tracker/track.py`.
- Blind lists: `independent/phrases.jsonl` (list 1), `independent2/` (list 2), `independent3/` (list 3) and
  `independent4/phrases_mixed.jsonl` (list 4, with the raw model output in `raw/` and `rejected_mixed.txt`) are the
  originals. Lists were read only after their runs; list 4's lines were not read for this archive (scanned by program).
- `prs/eval-pr3/README.txt` and `prs/eval/kw-after.log` mention a session scratchpad; the sections file they point at
  was not kept (see above).
- Texts in `root/` and `prs/` are the drafts, not always the posted versions: they still carry `{ISSUE}` / `{PR1}`
  placeholders, `.claude/drafts/...` and `<drafts>` paths, which `post.py` fills or upstream could not see.
- `root/issue-local-ai-startup.md` and `root/issue-chat-scroll.md` were posted as #323 and #324 (from the live test).
  They hold no personal data; the first names the owner's CPU and GPU, which is public in #323.
- `root/upstream-search-methods.md` (§12 and line 189) says some tuning scripts, kept in a session scratchpad, were "not
  archived: not recorded": they are not in this batch either.

| Folder / script | What it did | Output, and where the numbers went |
|---|---|---|
| `triage/cases.py`, `score.py`, `kwserver.py` | the 159-topic / 362-question test set (253 clean, 22 counterexamples, 109 typo) and its scorer over `/api/retrieve`; keyword-only server | `triage/RESULTS.md`; FORK.md 3k; became `tools/search_eval/` in PR 1 (#402) |
| `triage/build_split.py`, `compare.py`, `COMPARE_long_pages.md`, `COMPARE_rewrite.md`, `score_rewrite.log` | whole-book pages: length penalty (26 → 19) against the section split (26 → 4) | FORK.md 3k, PR 2 (#403) |
| `triage/typofix.py`, `cases_glued.py`, `glued_eval.py`, `glued_compare.py`, `glued/` | no-model typo correction against the library's words; glued words and gibberish, before/after | FORK.md 3k (99 of 109 typo questions changed, 0 of 253 clean; 20 of 24 glued split), PR 3 (#404) |
| `triage/convos.py`, `multiturn.py`, `mt_oldfork.py`, `turnhits_eval.py`, `MULTITURN.md`, `turnhits_*.txt` | the 52 conversations scored on the last message, several strategies | FORK.md 3k conversations table, PR 8 (#409) |
| `triage/conf_*.py`, `conf_*.txt`, `conf_*oof*.json`, `conf_top3_coef.json`, `CONFIDENCE.md`, `unit_conf_*.txt` | the search-confidence model: signals, grouped CV, calibration, thresholds 0.60 / 0.25, chat policy | FORK.md 3l, PR 5 (#406) |
| `triage/cases128.py`, `cases154.py`, `cases241.py`, `run154.py`, `run_sets.py`, `analyze154.py`, `analyze_sets.py`, `RESULTS_154.md`, `LESSONS_154.md/.json`, `r128/`, `r154/` | #128's, #154's and #241's questions labelled for the scorer and run through every version | FORK.md 3h–3k; `root/issue-search-tiers.md`, `root/comment-154-on-167.md` |
| `triage/ab_phrases_run.py`, `ab_phrases_analyze.py`, `AB_PHRASES.md/.json`, `rab/ab_tables.md` | four-arm A/B of the fire/water phrase fixes inside injury questions | FORK.md 3h ("Later bug: the phrases inside injury questions": first right 150 → 153, #154's count 144 → 168) |
| `triage/body_eval.py`, `body_analyze.py`, `BODY_SIGNS.md/.json`, `patch_guard_check.py`, `urgent_check.py` | body signs and phrase exceptions, before/after on every set | FORK.md 3k/3l, PR 7 (#408) |
| `triage/run_unit.sh`, `unit_*.txt`, `forktest_index_before.txt` | unit-test runs per commit; listing of the test data folder's index files | notes only |
| `independent/` (list 1), `independent2/` (list 2, 606 lines), `independent3/` (list 3, 531), `independent4/` (list 4, Qwen3.5-9B, Spanish and mixed) | blind held-out lists: `*_eval.py` runs, `analyze*.py` scores, `RESULTS.md`, `runs/report.txt`, `results.json`; list 4's `PROMPTS.md`, `recover.py` (cleans messy model output without reading it) and `english4.py` (English search words made once with the local model) | FORK.md 3l (lists 1, 2), 3m (list 3), 3i and Open (list 4: red 27% → 96%); PR 1 as `lists/list1..4.jsonl` |
| `heldout-fixes/` | fixes made from list 1 (4ea2d9f → 19c2db2): `heldout_eval.py`, `insample_eval.py`, `compare.py` | FORK.md 3k/3l; list 1 is in-sample afterwards |
| `contractions/` | n't / 's / 've forms put back before correction, before vs after on lists 1, 2 and in-sample | FORK.md 3k "Contractions without the apostrophe" |
| `meaning/` | the meaning-based red check: examples written before any list was opened, cross-validation, evaluation, runner (GGUF q8_0) against ONNX int8, cost; `hf/` model card and licence | `meaning/RESULTS.md`, `LLAMACPP_*.md`; FORK.md 3m; HF `STAirye/lastbook-meaning-red` |
| `urgent-mapping/` | the fork's urgency rules mapped onto #167's `urgent` field, measured on the lists | `RESULTS.md`, `measure_out.json`, `proposed_urgent.json`; PR 7 (#408) |
| `prs/` | `BRIEF.md`, the texts `0-issue.md`, `1..8-*.md`, `post.py`, `post_state.json`; `eval/` (PR 2) and `eval-pr3/` (PR 3) scripts and `.log` outputs | issue #401, PRs #402–#409 |
| `root/check_search_tiers.py` and its two result files | #154's 32 questions, top 8 on two servers | FORK.md 3h |
| `root/ab_embed.py`, `ab_embed_results.json`, `report-2026-11-18-hybrid-and-embed-ab.md` | bge-small vectors from onnxruntime against the runner's `--embed`; the overnight hybrid-index report | FORK.md 3m (runner `--embed`), PR 6 (#407) |
| `root/upstream-*.md` | the proposal summary, the methods and formulas, the first summary | the text behind #401 and `docs/TRIAGE-SEARCH.md` |

**Personal-data replacements.** Every other file is byte for byte the draft. Every file was scanned (JSON, logs and
the blind lists included, by program) for the owner's first and last name, `gmail`, e-mail addresses, user-folder paths,
tokens (`hf_`, `ghp_`, bearer), and home addresses; nothing else was found.
- `<scratchpad>`: `prs/eval/kw-after.log` line 1 (a session scratchpad under the user folder) and
  `triage/mt_oldfork.py` line 11 (`<scratchpad>/vocab.json`, the typo vocabulary cache; `typofix.py` builds one).
- `<user>`: `triage/forktest_index_before.txt`, the file-owner column of an `ls -la` (7 lines).
- `<owner>`: `triage/CONFIDENCE.md` ("Decided by <owner>") and `independent4/recover.py` (a docstring line).
- Kept: the alias STAirye, `noreply@...` addresses, `/home/tester` (a test user inside the Linux container).

### `linux-build-3m/` (FORK.md §3m Open "Linux, 2026-11-21", and PR 6, 2026-11-22)

A separate batch: it has its own purpose (build and check the runner and the `.deb` on Linux, in Docker
`debian:13-slim`) and its own dates. `inside.sh` builds `lastbook-llm` and the `.deb` from a clean clone mounted at
`/src` and checks `--embed`; `inside2.sh` reuses the runner and builds the `.deb`; `inside3.sh` builds PR 6's tree
(`pr6.tar`) and compares its `--embed` with the fork's; `smoke_deb.sh` installs the `.deb` in a fresh container and
plays a generated video.

| File | What it is |
|---|---|
| `inside.sh`, `inside2.sh`, `inside3.sh`, `smoke_deb.sh` | the scripts above |
| `run.log`, `run2.log`, `run3.log`, `smoke.log`, `app-build.log`, `cmake-linux.log`, `build-pr6.log` | their short logs (runner builds, the `.deb` scan, the smoke test) |
| `embed*.out`, `embed*.out.err` | `--embed` replies and loader messages: unit vectors of 384 (PR 6 against the fork's build) |
| `shots/` | seven 1360x900 screenshots of the installed app in the container: the setup screen, Videos, a generated test-pattern video. They show Lastbook's own screens and no personal data. Four are byte-identical (`library-home`, `library-map`, `library-videos`, `videos-page`) |

Not archived: the `.deb` (31 MB), `bin-linux/` (the runner build), `pr6.tar`, `model/`, `packs-manifest-v1.json`,
`apt*.log` and `build-linux.log` (56 KB, regenerable with `inside.sh`). Traps: `/src`, `/out` and `/w` are bind mounts
(a clean clone of `D:\git\lastbook`, `D:\git\lastbook\derived\linux-build`, a scratch folder) set by a `docker run` command
that was not saved; `inside*.sh` strip CRs with `sed` and need the meaning-red GGUF from `derived/models/meaning-red`.
`derived/` is git-ignored in the repo.

### `gpu-index-build-510/` (upstream PR Immortal-Protocols/lastbook#510, 2026-11-25 to 2026-11-27)

The GPU build of the meaning index: `python retrieval.py` tries CUDA (onnxruntime-gpu), then DirectML
(onnxruntime-directml), then the CPU, and `tools/embed_bench.py` measures the layers on any computer. This is upstream
work, not a fork change, so it has no FORK.md section; the code is on branch `gpu/index-builder` (commits da435ea,
b972946, c6aeaf0, 9dcd6ae). **Archived while #510 was still open** (asked for on 2026-11-27, to keep the scripts safe),
not after it closed as rule 1 says. The CPU-vs-GPU timed full builds and the 3,258-question comparison came earlier, from
PR 1's evaluation (`tools/search_eval/baseline-files.md` upstream), not from this batch.

| File | What it did | Output |
|---|---|---|
| `smoke.py` | 480 passages through `retrieval.Embedder` with CUDA and with `LASTBOOK_EMBED_DEVICE=cpu`: 730 vs 24 passages/s, lowest cosine 0.99999976; also against the stored index vectors | printed |
| `smoke_nopreload.py` | the same without calling `preload_dlls()` itself, to show the branch's own preload finds the CUDA libraries: 715 vs 26 passages/s | printed |
| `vk.py` | 3,000 passages (every 112th active chunk) with onnxruntime CPU/CUDA or the runner's `--embed` mode (CPU or Vulkan): the 20 / 629 / 25–32 / 188 passages/s table | `v_<mode>.npy`, `ids.npy` (not archived) |
| `cmpvk.py` | cosines of those vectors against onnxruntime CPU, 10-nearest overlap, runner vs `tokenizers` token counts on 400 passages | printed |
| `dml.py` | the same 3,000 passages with DirectML (batch 16/48/128): 242 / 320 / 356 passages/s, lowest cosine 0.9999998 | `v_dml<batch>.npy` (not archived) |
| `RESULTS-directml.md` | the DirectML write-up | |
| `bench/*.json` | `tools/embed_bench.py` runs: `global` (CPU only), `cuda`, `dml` (the PR's three-layer table), `cuda2` (first whole-build estimate, rest 72.6 min), `cuda3` + `cuda3.txt` (after the immutable fix; rest 68.5 min, whole build CUDA 76 min against 65 timed) | |
| `bench/before.txt`, `after.txt` | the index folder listed before and after `cuda3`: identical, so the tool wrote nothing. **Changed on archiving:** the file owner (the Windows user name) is replaced with `<user>` | |
| `prs/gpu-builder.md` | the PR text as drafted (title on line 1); `prs/pr510-body.md` is the body as last posted (with the checklist); `prs/gpu-builder.v1-cuda-only.md` the CUDA-only version before DirectML | |

Found on the way, and recorded in `.claude/drafts/TODO.md`: no test or check of a built meaning index exists upstream;
packs never ship the index (no model ships, so the vectors could not be used); the runner layer (Vulkan on Linux,
Metal on a Mac) is parked until someone with that hardware can test it.

Traps:
- The scripts use absolute paths: the branch at `D:\git\lastbook-pr\gpu-builder`, the data folder
  `D:\LastbookData-main-index` (read only), onnxruntime-gpu installed with `pip --target` into
  `D:\git\lastbook\.claude\drafts\prs\eval-pr1-main\ortgpu`, and the runner and q8_0 GGUF under `D:\git\lastbook\derived\`.
  `smoke*.py` also put a nonexistent `D:\git\lastbook-pr\eval-pr1-ortgpu` on the path (harmless).
- `smoke*.py`, `vk.py` and `dml.py` need `LASTBOOK_DATA` set to the data folder, or `retrieval` finds no model.
- `vk.py` and `cmpvk.py` call `retrieval.Embedder(gpu=True)` and `preload_dlls()` as the branch was on 2026-11-25; the
  runner binary they used predates the final #407 (its `ready` message has no pooling or dimension).
- The first `embed_bench.py` runs (`global`, `cuda`, `dml`, `cuda2`) opened the index with `mode=ro`, which on a WAL
  database created and touched `semantic.sqlite-wal` and `-shm` in the read-only data folder (the listings show them).
  They held no data and were deleted on 2026-11-27 after `quick_check` passed; the tool now reads with `immutable=1`.
- Not archived: the `.npy` vectors (37 MB), `ortdml/` (onnxruntime-directml, 72 MB) and the `ortgpu/` wheels. They stay
  in `D:\git\lastbook\.claude\drafts\gpu-builder\` and `...\prs\eval-pr1-main\`; the scripts regenerate the vectors.
