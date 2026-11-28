# Results

## Rerun 2026-11-27, main 51658f5 (after #322, #326, #327, #330, #331, #332, #335, #430, #432, #455 merged)

```
python3 -B tools/guide_search_bench/bench.py --units --out bench.json A=origin/main B=origin/main+328+338+339 \
  C=origin/main@web/words.js D=origin/main+328+338+339@web/words.js \
  A347=origin/main+347 C347=origin/main+347@web/words.js
```

Arms: A = main; B = main + the guide PRs still open (#328, #338, #339; all clean); C = main + this branch's
`web/words.js` (main's `web/words.js` has not changed since 4cb8a20, so the rule applies as it is); D = B + C; A347
and C347 = main + #347's tests, without and with the rule.

| set | A | B | C | D | C vs A (A only : C only) | D vs B |
|---|---|---|---|---|---|---|
| #430's 17 false matches | 11 | 12 | 12 | 13 | 0 : 1, p = 1 | 0 : 1, p = 1 |
| other #333 / #432 searches (24) | 13 | 13 | 16 | 16 | 0 : 3, p = 0.25 | 0 : 3, p = 0.25 |
| held-out traps (67) | 21 | 21 | 25 | 25 | 1 : 5, p = 0.22 (clustered 0.375) | 1 : 5, p = 0.22 |
| held-out useful prefixes (59) | 49 | 49 | 49 | 49 | no change | no change |

- **#430's rows.** The merged guide PRs fix 11 of 17. The rule adds `war` only, and #328 adds `want to die`.
  Still wrong in every arm: `ear infection`, `head lice`, `bat in house` and `car stuck in snow`. Under the rule,
  `head lice` and `bat in house` leave their unrelated guide, but not for a right one.
- **Other searches.** The rule adds `ear pain`, `bat` and `mold after flood`.
- **Held-out traps.** The rule fixes `ear bleeding`, `war zone`, `civil war`, `loo roll` and `the loo is blocked`,
  and loses `pot plants` (now the wild-plants choice). The same gain holds on top of B.
- **Controls.** Main's test assertions that fail under the rule:
  - `volcanic ash` and `fires after an earthquake`: real losses, unchanged.
  - `generator gas can storage` and `bleeding won't stop after a chainsaw accident`: pinned emergency baselines
    move, unchanged.
  - `ice pack`: new. Main now pins it to the suspicious-package choice ("pack" starts "package"); the rule gives the
    packing choice. Both are wrong by reference.json (sprain or heat illness), so it is not counted as a loss.
  - B and D also fail `test_context_never_holds_a_life_threat` on #328's context entry `live`; B's own suite passes.
- **#347's tests.** They pass on main. Under the rule, all 11 of its useful prefix searches hold (`cook`, `warm`,
  `dry`, `air con`, `car battery` …). Its known-misses check fails for 6 of the 7 listed searches: `want to die`,
  `ear infection`, `ear pain`, `head lice`, `bat in house` and `war` no longer open the unrelated choice. That is the
  change the list is meant to flag, but only `war` lands on a right answer. `out of diapers` does not move.

So on current main the rule's case is the held-out traps (5 : 1) and `war`, against the same two control losses.
A narrower revision would need to keep those gains, fix `volcanic ash` and `fires after an earthquake`, and leave
`ice pack` as main pins it.

## Rerun 2026-11-24, main 4cb8a20, with #455 in arm B

The command in `README.md` at that commit. Arms: A = main; B = main + #322, #326, #327, #328, #330, #331, #332, #335, #338, #339,
#432, #455 (all clean); C = main + this branch's `web/words.js`; D = B + C. Count = searches whose first result is
right. p = exact McNemar on the discordant pairs (in brackets: clustered by short word, exact).

| set | A | B | C | D | C vs B (B only : C only) | D vs B |
|---|---|---|---|---|---|---|
| #430's 17 false matches | 0 | 12 | 7 | 13 | 6 : 1, p = 0.125 (0.19) | 0 : 1, p = 1 |
| other #333 / #432 searches (24) | 7 | 13 | 14 | 16 | 3 : 4, p = 1 (1) | 0 : 3, p = 0.25 |
| held-out traps (67) | 19 | 21 | 24 | 25 | 1 : 4, p = 0.375 (0.5) | 1 : 5, p = 0.22 |
| held-out useful prefixes (59) | 46 | 49 | 46 | 49 | 3 : 0, p = 0.25 | 0 : 0 |

Against main: B 12 : 0 on #430's rows (p = 0.0005), C 7 : 0 (p = 0.016; clustered 0.063), D 13 : 0 (p = 0.0002).
On the held-out traps: B 2 : 0 (p = 0.5), C 6 : 1 (p = 0.125), D 7 : 1 (p = 0.07).

**#430's rows.**
- C fixes `stomach pain`, `left arm pain`, `fall from ladder`, `the loo wont flush`, `rat bite`, `rat poison` and
  `war`.
- B fixes all of those except `war`, plus `elderly fall`, `want to die`, `what to pack`, `out of formula`,
  `ran out of insulin` and `high fever`.
- D adds `war` to B.
- No arm fixes `ear infection`, `head lice`, `bat in house` or `car stuck in snow`.

**Controls.** #430's 9 KEEP rows hold in every arm. Main's test assertions that fail:

| search | B | C | D |
|---|---|---|---|
| `volcanic ash` (volcano → wildfire smoke; relied on ash/ashfall) | pass | **fail** | **fail** |
| `fires after an earthquake` (earthquake, after → home is damaged; relied on after/aftershocks) | pass | **fail** | **fail** |
| `generator gas can storage` (pinned baseline: small engines → run a generator safely; still not Poisoning) | pass | fail | fail |
| `bleeding won't stop after a chainsaw accident` (pinned baseline: earthquake → shock; an improvement) | pass | fail | fail |
| `test_context_never_holds_a_life_threat`: context entry `live` (structural, from B's content; B's own suite updates it) | fail | pass | fail |

B passes its own suite. D fails B's own suite in the four searches above and five more. B pins these to results
that came from a start-of-word match: `dog wants to die`, `my dog wants to die`, `dog not breathing i want to die`
and `cat is not breathing and i want to die` keep "special diets" listed (die/diets), and `ice pack` is pinned to
the suspicious-package choice (pack/package).

## What changed since the #333 comment of 2026-11-24 17:49 UTC

- B now includes #455. That moves `rat bite`, `out of formula` and `ran out of insulin` to their right answers in
  B (and in D). Nothing else changes in any set.
- #430's rows: B 9 → 12, D 11 → 13. C vs B was 2 : 4 (p = 0.69); it is now 1 : 6 (p = 0.125). B is ahead on the
  rows it was written for, still not significantly. D's gain over B is now 1 : 0 (`war`) instead of 2 : 0
  (`rat bite` is now in B).
- Secondary, held-out traps and held-out prefixes: unchanged.
- Controls: same losses as before. The earlier run also reported 7 failures of `test_validate_topics` in every
  arm. They came from the old harness's partial copy of the repository, not from any arm, and are gone.
- The two real control losses for the rule (`volcanic ash`, `fires after an earthquake`) are still open.

## Variant sweep (`sweep.py`, development sets only)

| variant | #430's rows | other #333 | searches failing a test |
|---|---|---|---|
| last word only, 0.5 | 7 | 14 | 6 |
| others 0.25, last 0.5 | 7 | 14 | 5 |
| last word only, 0.75 | 6 | 12 | 5 |
| last word only, 1 | 4 | 9 | 6 |
| last word only, 0.5, no endings | 7 | 14 | 10 |
| last word only, 0.5, with stems | 7 | 13 | 22 |
| last word only, 0.5, no joining | 7 | 14 | 8 |
| **every word 0.5 (the rule)** | **7** | **14** | **4** |

The rule was fixed before the held-out set first ran. It is still mildly in-sample on #430's rows and on the
controls, which is why the held-out set is the comparison to weigh most. 17 rows is a pilot: an exact McNemar test
needs at least a 6 : 0 split to reach p < 0.05.
