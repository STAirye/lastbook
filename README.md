# Data: long pages in sections (triage search, part 2, Immortal-Protocols/lastbook#403)

These are the full `tools/search_eval/score.py --rows` outputs behind the sensitivity and own-index tables in
`docs/TRIAGE-SEARCH.md` §1 of #403: one row per question, with its top-8 titles. The scripts that made them, and how to
rerun them, are in `tools/search_eval/sections_sweep/` on #403's branch. `SHA256SUMS` lists every file. The files are
stored byte for byte (`.gitattributes`: `* -text`).

| File | What it is |
|---|---|
| `main_keyword.json`, `main_hybrid.json` | `main` (part 1's baseline runs): keyword, and hybrid on `main`'s meaning index (338,910 passages, `text_sha256` 938e417e…) |
| `keyword_L<LONG>_S<SECTION>.json` | this part, keyword, with `engine.sections.LONG` / `SECTION` set to those values (9 pairs) |
| `hybrid_main_index_L20000_S5000.json` | this part, hybrid, on `main`'s meaning index (read-only, so long pages' passages keep their whole-page label) |
| `hybrid_own_index_L20000_S5000.json` | this part, hybrid, on an index built by this part's own indexer (340,532 passages, `text_sha256` c00f64f9f68f0d446d9476ce797a9da56cf601d388b994a62f987ce8675ffaf0; built on a GPU) |

Data: the published `Lastbook-Medium.zip` (SHA-256 e4ef75af…876068a, as in `manifest-v1.json`). The keyword runs and
the own-index hybrid run used #403's branch rebased onto `main` d223056; `hybrid_main_index` was run on the same part's
code before the rebase (on `main` 9645686), whose keyword results are identical on all 3,258 questions.

Reproduce the tables:

```
python -B tools/search_eval/sections_sweep/analyse.py --base main_keyword.json --runs . --base-hybrid main_hybrid.json --hybrid hybrid_main_index_L20000_S5000.json hybrid_own_index_L20000_S5000.json
```

## Review of 226802c: the sections index getting in the way (`review-403/`)

Before-and-after captures for the two cases reported on #403, fixed in 906eb1b, taken through the app's own HTTP API
(`/api/find`, then `/api/doc` and `/api/page` for the first long web page cited) on the Medium pack, server run with
`--no-index`.

| File | What it is |
|---|---|
| `capture.py` | Run 1: the sections file removed, the server started, the first search sent at once, then every 2 s until it cites sections (at most 60 s). Run 2: a good sections file put back with its `pages` table dropped (`long` and `section` still readable), the server restarted, the same searches |
| `before.json` | the two runs on 226802c |
| `after.json` | the two runs on 906eb1b |
| `summarise.py`, `captures.md` | the tables posted on #403, from the two JSON files |
| `recheck_keyword_L20000_S5000.json` | `score.py --rows` on 906eb1b at the default pair: identical, row for row, to `keyword_L20000_S5000.json` (3,258 of 3,258) |

```
python -B review-403/capture.py <checkout> <spare data folder> <label> <port> <out.json>
python -B review-403/summarise.py review-403/before.json review-403/after.json
```

`capture.py` writes the sections file in the data folder's `derived/index`: use a spare data folder.
