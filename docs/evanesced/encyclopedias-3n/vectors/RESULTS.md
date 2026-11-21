# Per-file vector index for MDWiki: prototype results (2026-11-20)

Files here: `build.py` (walk, cut, embed on the GPU, write the sidecar, time a CPU sample), `bench.py` (runner-vs-GPU
check, query timing, keyword/vector/hybrid benchmark), `bench.json` (every row), `build_full.log`.
Sidecar: `D:\LastbookData\derived\index\vec-mdwiki_en_all_maxi_2025-11.zim-2302838768-1792967166000000000.*`
(keyed by the ZIM's size and mtime_ns). Nothing written into the ZIM or library; nothing committed or pushed.
(Written in this session's worktree `.claude/`, because a hook blocks writes to the base repo's `.claude/`.)

## Counts
- libzim `all_entry_count` 473,338 (the 363,797 "entries" figure is articles+redirects; the rest are images/css/js).
- Redirects skipped: 292,097. Non-HTML resources, print versions, articles over 800,000 bytes (the picker's own rules): 109,880.
- **Articles indexed: 71,361. Sections (5,000 chars): 213,787** (about 3.0 per article).

## Build
- Smoke test (2,000 articles, 8,199 sections): 27 s, no crash; extrapolated 213k sections to about 11 min of embedding.
- **Full GPU build (RTX 3080 Ti, fp16, batch 128): 385 s total (6.4 min)**, of which 357 s was embedding; text extraction ran in 10 worker processes.
- **CPU-only estimate**: 500 random sections took 24.4 s with torch on CPU (fp32, batched, all cores), 48.9 ms/section, so about **2.9 h** for the whole file.
  (Through the app's runner, one text at a time: 123-193 ms/section in the 150-section check, so about 7-11 h. A CPU build should not use the runner.)

## Size
| part | size | share of the 2.30 GB ZIM |
|---|---|---|
| vectors f16 | 164.2 MB | 7.1% |
| vectors int8 (x127, one byte per dim) | 82.1 MB | 3.6% |
| rows (path, title, article index, section start) | 5.1 MB | 0.2% |

## Runner vs GPU vectors
`meaning_red.Model.embed` (q8_0 GGUF, `--cpu-only`) against the stored fp16 GPU vectors, 150 random sections:
cosine min 0.9996, median 0.99985, none under 0.99. Same space, so the runner can embed the question.

## Query time (253 questions, runner embed + brute-force scan of 213,787 x 384, warm)
| step | median | p90 |
|---|---|---|
| question embed through the runner | 10.6 ms | 12.7 ms |
| scan, f32 matrix in memory (328 MB RAM) + best section per article + top 10 | 13.8 ms | 14.2 ms |
| **total** | **24.4 ms** | **26.4 ms** |
| scan from int8, dequantised in chunks (82 MB RAM) | 83 ms | 86 ms |
(Top-3 articles from int8 equal the f16 ones in 33 of 40 queries; int8 would need a better quantiser or a rerank. Not a reason to prefer it at this size.)
For comparison the keyword picker took 270-295 ms median, 460-600 ms p90 on this machine (MDWiki only, 3 articles read and cut).
Excerpt reading for the 3 hits (re-opening the article, about 10-30 ms) is not in the vector figures.

## Benchmark (invented questions from `triage/cases.py`, clean phrasings; scorer = `compare.py`: topic `need` patterns match excerpt or title)
Keyword = `wiki_pick.pick`, limited to MDWiki (a library root holding only a hard link to it: `D:\LastbookData\tmp-mdwiki-only`, safe to delete).
Vector = top 3 articles by best-section cosine, same excerpt step as the picker (`pick_section` of the best section, 2,000 chars).
Hybrid = vector top-10 articles plus the keyword picker's candidates, ranked by cosine. Hybrid2 = same candidates, ranked by cosine + 0.3 x the picker's score.

| set | n | method | first article useful | any of 3 useful | no result |
|---|---|---|---|---|---|
| non-red | 122 | keyword | 79 (64.8%) | 99 (81.1%) | 6 |
| non-red | 122 | **vector** | **84 (68.9%)** | **108 (88.5%)** | 0 |
| non-red | 122 | hybrid | 84 (68.9%) | 108 (88.5%) | 0 |
| non-red | 122 | hybrid2 | 85 (69.7%) | 108 (88.5%) | 0 |
| red (skip encyclopedias in the app) | 131 | keyword | 62 (47.3%) | 80 (61.1%) | 13 |
| red | 131 | **vector** | **82 (62.6%)** | **109 (83.2%)** | 0 |
| red | 131 | hybrid | 82 (62.6%) | 109 (83.2%) | 0 |
| red | 131 | hybrid2 | 67 (51.1%) | 98 (74.8%) | 0 |

Notes
- Hybrid equals vector by construction: the global top-10 by cosine already contains anything the keyword candidates could outrank on cosine, so a cosine-ranked union adds nothing. Hybrid2 (blended) gains one first-article on non-red and loses on red; a fixed weight is not convincing.
- The vector index also finds an answer when the word search finds nothing (keyword returned nothing for 6 non-red and 13 red questions; vector always returns 3).
- Small sample (122 questions): a gain of 5 first-article answers (+4 points) on non-red is suggestive, not significant; any-of-3 +9 questions (+7 points) is firmer. The red gain is large but those questions skip encyclopedias in the app. The scorer is lenient (pattern in the excerpt or title), as in `compare.py`.
- Not measured: whether a vector hit that the patterns accept is actually better for the model's answer; the first-article metric on the full app (the vector index would only reorder the candidates).

## Verdict
Worth proposing as an optional per-file sidecar. A 164 MB (f16) index, built in 6.4 min on a GPU where the packs are made, makes a question about 24 ms total through the existing runner (against about 280 ms for the keyword picker), needs no model in the desktop process and no socket, and was equal or better on every column. Costs to weigh: about 330 MB RAM if loaded as f32 (or convert f16 chunk by chunk), a build step per encyclopedia file and version, and the rule that the index must match the ZIM's size and mtime or be ignored. A CPU-only build (about 3 h for MDWiki) is possible but slow; Wikipedia-sized files would need the GPU. Next steps if wanted: repeat on Appropedia and Wikibooks, test a cosine-plus-keyword blend on more questions, and compare the final answer quality.

---

# All three files (added 2026-11-20)

Scripts: `build.py` (now also skips Appropedia's translated paths `Article/es`, as the picker's `prefer_primary` does; MDWiki was built before this and has none that matter), `bench_all.py`, `bench_all.json`, `build_wikibooks.log`.
Same method and sidecar folder (`D:\LastbookData\derived\index\`). The temporary MDWiki-only root was deleted.

## Build
| file | ZIM size | articles | sections | GPU build | CPU-only estimate | f16 | int8 | rows |
|---|---|---|---|---|---|---|---|---|
| MDWiki | 2.30 GB | 71,361 | 213,787 | 385 s | 2.9 h | 164.2 MB | 82.1 MB | 5.1 MB |
| Appropedia | 0.58 GB | 13,956 | 26,395 | 31 s | 0.36 h (48.4 ms/section) | 20.3 MB | 10.1 MB | 1.3 MB |
| Wikibooks | 6.18 GB | 100,385 | 189,782 | 279 s | 2.55 h (48.3 ms/section) | 145.8 MB | 72.9 MB | 11.1 MB |
| **total** | 9.06 GB | 185,702 | 429,964 | **695 s (11.6 min)** | **5.8 h** | **330 MB** | 165 MB | 17.5 MB |

Appropedia smoke test (2,000 articles) ran first: 8 s, no crash. Appropedia: 65,156 entries, 8,417 redirects, 42,783 skipped (non-HTML, translations, print, over 800 KB).
Wikibooks: 385,302 entries, 16,574 redirects, 268,343 skipped (mostly non-HTML and print versions; the article count is after the picker's own skip rules).
The index is about 3.6% of the ZIM bytes (f16) overall.

## One question across all three
The runner embeds the question once, each file's matrix is scanned, the top 3 articles per file are merged by best-section cosine.
| | median | p90 |
|---|---|---|
| runner embed | 9.0 ms | |
| scan of three files, f32 in RAM | 26.6 ms | 27.4 ms |
| **total (f32)** | **35.8 ms** | **37.5 ms** (nonred; red 35.6 / 36.9) |
| scan with f16 kept in RAM, converted to f32 in chunks of 50,000 rows | 416 ms | 433 ms (100 questions) |
| picker, all three files (wiki_pick.pick) | 444 ms nonred, 514 ms red | 736 / 883 ms |

RAM: f32 total **630 MB** (MDWiki 313, Appropedia 39, Wikibooks 278); f16 total 315 MB plus a 73 MB chunk buffer.
The chunked f16 scan is 15x slower than f32 because numpy converts half precision without SIMD, so it is not a good middle path.

What I would ship: the **f16 file on disk** (330 MB for these three, 3.6% of the ZIMs), loaded as f32 **lazily on the first question that reaches encyclopedias, and only for the files present** (630 MB peak for all three; the app already runs a CPU model, and the number scales with the pack, not the question). If 630 MB is too much for the low-RAM target, the options are: int8 in RAM (165 MB total; scan about 80 ms per 214k rows per my earlier test, so about 170 ms for all three, but top-3 matched f16 in only 33 of 40 queries, so it needs a rerank by f16 for the top 20 rows), or a smaller index with fewer sections per article (for example only the first N sections of long books). I did not test either beyond the numbers above.

## Benchmark, all three files (real root, `wiki_pick.pick` searches all three)
Same invented questions and scorer as above.

| set | n | method | first useful | any of 3 useful | none | time median / p90 |
|---|---|---|---|---|---|---|
| non-red | 122 | keyword | 85 (69.7%) | 108 (88.5%) | 0 | 444 / 736 ms |
| non-red | 122 | **vector** | **102 (83.6%)** | **113 (92.6%)** | 0 | **36 / 38 ms** |
| red | 131 | keyword | 61 (46.6%) | 89 (67.9%) | 5 | 514 / 883 ms |
| red | 131 | **vector** | **92 (70.2%)** | **111 (84.7%)** | 0 | **36 / 37 ms** |

Which file holds the top (first) article:
| set | method | MDWiki | Appropedia | Wikibooks |
|---|---|---|---|---|
| non-red | keyword | 44 | 46 | 32 |
| non-red | vector | 33 | 28 | **61** |
| red | keyword | 65 | 32 | 29 |
| red | vector | 46 | 17 | **68** |

Wikibooks does take more first places with vectors (50% of non-red, 52% of red, against 26% and 22% for the keyword picker). It does not look like crowding that hurts, because the first article was useful more often (102 vs 85 and 92 vs 61), but the scorer only checks that topic words appear in the excerpt or title. Wikibooks first articles are cookbook, survival or first-aid book chapters, which suits many of these questions; I did not read the answers for quality, and the medical questions are where MDWiki's authority matters. Worth reading the rows in `bench_all.json` where the vector top article is Wikibooks and MDWiki's was also useful before deciding on a per-file bonus (for example, a small cosine bonus for MDWiki on medical topics).
The hybrid was not repeated here: on MDWiki a cosine-ranked union was identical to vector, and the blend did not help.

## Updated verdict
Stronger than the MDWiki-only result. Across the three files, the first article is useful for 84% of non-red questions (picker 70%) and 70% of red ones (picker 47%), in about 36 ms against 440-510 ms, with no result missing. A per-file sidecar built once where the packs are made (12 min on one GPU for these three, 330 MB in f16) is worth proposing upstream. Open points for the proposal: RAM (630 MB as f32 for all three, scaling with the packs; chunked f16 is too slow in numpy), the Wikibooks share of first places, a stale-index rule (size and mtime in the file name), and a CPU-only fallback for pack makers without a GPU (about 6 h for these three). The test set is 253 invented questions with a lenient pattern scorer, so these are differences in how often a useful article comes first, not a measure of answer quality.
