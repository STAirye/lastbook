# Guide-search benchmark (#333)

A paired benchmark for changes to the guide search (`web/words.js` `rankTopics`, the "Start with a guide" list).
It compares several versions ("arms") on the same searches. The outcome is whether the **first result is a right
answer**, not merely a different one. The branch this lives on also carries the rule being tested: a start-of-word
match counts half (see the comment above `scorer` in `web/words.js`).

## Rerun

From the repository root, with `origin` pointing at Immortal-Protocols/lastbook (otherwise add `--remote NAME`):

```
git fetch origin main
python3 -B tools/guide_search_bench/bench.py --units --out bench.json \
  A=origin/main \
  B=origin/main+328+338+339 \
  C=origin/main@web/words.js \
  D=origin/main+328+338+339@web/words.js
```

On main 4cb8a20, arm B was `+322+326+327+328+330+331+332+335+338+339+432+455`. Most of those are merged now, so
B lists only the guide PRs still open. `RESULTS.md` has both runs.

- `A` is main.
- `B` is main with the listed guide PRs merged in that order, in a temporary worktree. Every merge must be clean.
- `C` is main's guides with this branch's `web/words.js`.
- `D` is B with this branch's `web/words.js`.

An arm is `BASE[+PR...][@words.js]`. Pull request heads are fetched from the remote as `pull/N/head` and kept under
`refs/guide-search-bench/`. Use `--dev` to leave the held-out set out while tuning.

`python3 -B tools/guide_search_bench/sweep.py` reruns the variant sweep that chose the weights. It uses the
development sets only.

Needs git, node and Python 3.9+. No library or data folder is needed.

## What is measured

| set | n | answers |
|---|---|---|
| primary | 17 | #430's false matches. #430's right answers where it has them; `reference.json`'s own for the rest, each with a one-line reason |
| secondary | 24 | the other #333 and #432 searches; exploratory |
| held-out trap | 67 | short words that start an unrelated longer guide word (`heldout.json`) |
| held-out keep | 59 | short or half-typed words whose longer guide word is the right one (`heldout.json`) |
| controls | ~4,600 | every search in `app/tests/test_topic_search*.py` of every arm, plus #430's KEEP rows |

`reference.json` and `heldout.json` were written before any arm ran. Their SHA-256 is in `FROZEN.sha256`, and
`bench.py` refuses to run if either changed. `.gitattributes` keeps their bytes as committed. The held-out answers
were judged by the author of the rule, so **they need an independent reader**. Corrections are welcome, but as a new
file with new hashes, not as edits to these.

An answer is `guide/choice`, `guide/` (the guide with no choice), or `NONE` (no guide: right only where it is
listed, which means where no guide covers the subject).

For the controls, a changed first result is listed but is not counted as a loss. A loss is a test assertion that
fails (`--units`). Arm A's test suite runs on every arm, and each merged arm's own suite also runs on that arm.
#430's test file is read from #430's pull request head at run time.

Statistics: exact McNemar on the discordant pairs, and the clustered McNemar of Durkalski et al. (2003), clustered
by the short word involved (pain, fall, rat …), with an exact sign-flip p.

Results of the last run: `RESULTS.md`.
