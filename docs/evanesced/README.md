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
the test questions' `cases.py`, still in the untracked drafts until the search-as-triage batch is archived), and reads
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
