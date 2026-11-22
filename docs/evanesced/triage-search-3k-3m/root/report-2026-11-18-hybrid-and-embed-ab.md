# Overnight results, 2026-11-18

The meaning-based index finished at 04:14: 337,016 passages from 7,808 documents, in about 4.6 h at ~20 passages/s on the CPU.

## 1. #154's 32 questions, keyword-only vs hybrid

Useful hits in the top 8 (title or excerpt matches the question's topic). Same script as the issue
(`check_search_tiers.py`); hybrid results in `check_search_tiers_results_hybrid.json`.

| Question | keyword: before → #128 | hybrid: before → #128 |
|---|---|---|
| burned my hand trying to light a fire | 4 → 2 | 6 → 4 |
| i burnt my fingers lighting the campfire | 5 → 4 | 5 → 5 |
| smoke inhalation from lighting a fire indoors | 6 → 4 | 8 → 7 |
| carbon monoxide from making a fire in the tent | 8 → 3 | 7 → 7 |
| my clothes caught fire while starting the fire | 2 → 1 | 5 → 7 |
| my kid fell into the fire while we were making a fire | 1 → 1 | 0 → 2 |
| **treat water in the lungs after drowning** | **5 → 0** | **5 → 2** |
| how do i treat water poisoning | 8 → 6 | 7 → 7 |
| light a fire to keep him warm with hypothermia | 4 → 0 | 4 → 3 |
| my son nearly drowned in the rainwater pool | 2 → 2 | 5 → 5 |
| someone fell in the rainwater pool and isn't breathing | 3 → 3 | 5 → 5 |
| he swallowed pool water and now he's coughing | 1 → 1 | 4 → 4 |
| my child swallowed lamp oil | 3 → 3 | 5 → 5 |
| i burned my hand on the camp stove | 3 → 3 | 7 → 7 |
| is it safe to put water on a burn | 3 → 3 | 5 → 5 |
| **someone got shocked by a wire in the flood water** | **0 → 0** | **0 → 0** |
| how do i light a campfire | 0 → 8 | 2 → 6 |
| i need to start a fire but i have no matches and no gas | 2 → 7 | 5 → 8 |
| how do i purify water from a creek | 0 → 1 | 5 → 5 |
| make a fire escape plan for my family | 6 → 3 | 6 → 6 |
| how do i treat water damage on the floor | 0 → 0 | 3 → 1 |
| **Total (of 256)** | **141 → 133** | **178 → 181** |

(Rows where all four numbers match, such as scorpion, snake and poison ivy, are left out.)

What it means:
- Meaning-based search lifts the baseline a lot (141 → 178) and absorbs most of #128's losses. With it on, #128 is
  roughly neutral overall (+3).
- It does not fix the worst case. "Water in the lungs after drowning" still loses 3 of its 5 first-aid pages to
  wastewater and chlorination manuals, because the phrase "treat water" still forces the keyword half onto water
  treatment. The tiered ranking in #154 is still needed.
- The flood-wire shock question is 0 on every setup: no electrical-injury page reaches the top 8. That is a gap in what
  the search reaches, not in ranking.
- Upstream ships no model, so most installs run keyword-only search. The keyword column is what most users get.
- The "water damage" row is upstream code; the fork already fixes it (0ace449).

## 2. A/B: onnxruntime (A) vs our runner with #168's `--embed` (B)

`ab_embed.py`, results in `ab_embed_results.json`. Sample: 2,000 random stored passages, 36 questions, top 10 over all
337,016 passages. B is `work-embed\bin-win\lastbook-llm.exe` (Vulkan build) with `bge-small-en-v1.5-f32.gguf`.

| | A onnxruntime CPU | B runner GPU | B runner CPU |
|---|---|---|---|
| Passages a second (batches of 16) | 29.6 | **119.0** | 27.0 |
| One question | 4.4 ms | 6.7 ms | 8.5 ms |
| Start-up (model load) | — | 0.31 s (69 ms load) | 0.17 s (25 ms load) |
| Cosine to the stored vector: median / p1 / min | 1.0 / 0.99991 / 0.99987 | 1.0 / 0.99991 / 0.99883 | 1.0 / 0.99991 / 0.99882 |
| Passages below 0.999 | 0 | 1 of 2,000 | 1 of 2,000 |
| Questions with the same best passage | — | 36 / 36 | 36 / 36 |
| Top 10 shared with A, mean | — | 9.97 | 9.97 |
| Question cosine A–B, min | — | 1.0 | 1.0 |

The two misses are one swapped 10th result each: "can food gone bad" on GPU and "burned my hand on the camp stove" on
CPU.

What it means:
- The runner gives the same search results as onnxruntime. The vectors are interchangeable, so an index built by one
  works with the other and nothing needs rebuilding.
- On the GPU the runner indexes **4× faster** (119/s vs 29.6/s). The 4.6 h build would be about 50 min. On the CPU it is
  as fast as onnxruntime (its 4 threads against onnxruntime's default).
- For one question both take under 10 ms, so search speed is the same.
- The model is 133 MB (F32 GGUF). An F16 version would be about 67 MB, but that is untested.

## State of things (nothing committed, pushed or posted)

- `.claude/worktrees/runner-embed` (branch `fork/runner-embed`): #168's `lastbook_llm.cpp` change is staged, not
  committed.
- The runner built with it is in `D:\buildtools\lastbook-llm\work-embed\bin-win\`. The app's own runner is untouched.
- Models are in `D:\LastbookData\derived\models\bge-small-en-v1.5\` (`model.onnx`, `tokenizer.json`, the GGUF). The
  official BAAI files are in `bge-small-en-v1.5-hf\`. All SHAs checked.
- Test servers are stopped.

Possible next steps:
1. Port #168's `RunnerEmbedder` to the fork for Windows, using the runner on the GPU for indexing, with onnxruntime as
   the fallback.
2. Add the hybrid column to #154, with the drowning and flood-wire rows as the evidence that ranking is still needed.
