# Results (rerun 2026-11-24, main 4cb8a20, with #455 in arm B)

The command in `README.md`. Arms: A = main; B = main + #322, #326, #327, #328, #330, #331, #332, #335, #338, #339,
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
