# #154's question set through every version (2026-11-18)

Scripts: `cases154.py` (labels), `run154.py` (in-process runner), `analyze154.py` (scoring). Raw runs in `r154/*.json`,
all scores in `RESULTS_154.json` (= `r154/analysis.json`). Read-only: sections build refused, read-only index connections,
vector file never truncated, no model, `python -B -X utf8`. No code, branch or data-folder changes.

| version | code | data |
|---|---|---|
| main | upstream `256d52f` (worktree `search-before`, verified) | `D:\LastbookData` |
| old fork | `8e201db` (existing worktree `table-reading-90d232`, verified) | `D:\LastbookData` |
| new fork | `fork/everyday-buttons` `9366f16` (worktree `everyday-buttons`) | `D:\LastbookData-fork-test` (sections built) |

Each in keyword-only (`retrieval.AVAILABLE=False`) and hybrid (337,016 passages loaded in all three hybrid runs). Old
versions: top 8 of `assistant.hybrid(q[:200], 8)`, what `/api/retrieve` returns. New fork: `assistant.turn_hits` on the
question alone (route `first`, the chat's first search; same 8 pages as `hybrid`, checked for all 64 queries), plus its
`confidence` and `danger` (`is_danger`).

## Read this first: this is NOT an out-of-sample test

- **#154 is our own issue** (author STAirye). Upstream has no separate list and no expected answers: the only
  maintainer comment asks us to open a test-only PR *with* "expected first results". The 32 questions are the ones in
  `check_search_tiers.py`, which we wrote.
- **29 of the 32 questions are in `cases.py` verbatim** (all except "smoke inhalation from lighting a fire indoors",
  "he swallowed pool water and now he's coughing", "how do i treat a burn from a campfire"). They were among the 362
  questions `conf_fit.py` fitted, so the committed coefficients in `engine/confidence.py` have seen them. Run with the
  committed coefficients, the confidence numbers below are mostly **in-sample**.
- Closer to out-of-sample: (a) the **32 typo variants** written for this run (none is in `cases.py`; the topics are);
  (b) the stored **grouped-CV out-of-fold** probabilities in `conf_oof_<mode>.json` for the 29 overlapping questions
  (their topic's fold was held out). Both are reported.
- Labels were written blind (below), but 27 of 29 colours and 24 of 29 first needs match `cases.py`'s own labels, so the
  label side is not independent either.

## Labels (blind)

`cases154.py`: colour, `need`, `context`, `not_first` and a panicky typo for each question, written from the question's
meaning before any of this run's results were opened (the issue's aggregate before/after counts had been read).
13 red, 11 yellow, 8 green. Two new need patterns: `FIRESPREAD`, `WATERDAMAGE`. `not_first` only where the emergency word
has an everyday meaning (light a campfire, start a fire "no gas", escape plan, fire spread, water damage, poison ivy).

Checked afterwards against `cases.py`: colours differ on 2 ("my kid fell into the fire..." and "light a fire to keep him
warm with hypothermia": red here, yellow there); need order differs on 3 (water poisoning, isn't breathing, formula); a
different need on 2 (fire spread: here fire behaviour, there escape/wildfire/drill; water damage: here water-damage
cleanup, there flood prep).

Label noise: `first_ok` is a regex on title+excerpt. "is it safe to put water on a burn" counts as right with a seizure
page first (its excerpt says "burn"); "how do i light a campfire" counts as right on main keyword-only because the first
title says "campfire", although #154's stricter pattern gives it 0 of 8.

## 1. #154's own count (useful of 8 by its topic regex, total of 256)

Main reproduces the earlier numbers exactly: **141** keyword-only and **178** hybrid, question by question (no
differences against `check_search_tiers_results*.json`'s "before"). The earlier "after" (#128 alone) was 133 / 181.
"F" = first result right by the triage label.

| Question | colour | kw main | kw old fork | kw new fork | hy main | hy old fork | hy new fork |
|---|---|---|---|---|---|---|---|
| burned my hand trying to light a fire | yellow | 4 | 2 | 2 | 6 | 4 | 4 |
| i burnt my fingers lighting the campfire | yellow | 5 F | 4 | 3 | 5 F | 5 F | 5 F |
| smoke inhalation from lighting a fire indoors | red | 6 F | 4 F | 4 F | 8 F | 7 F | 7 F |
| carbon monoxide from making a fire in the tent | red | 8 F | 3 F | 3 F | 7 F | 7 F | 7 F |
| my clothes caught fire while starting the fire | red | 2 | 1 | 1 | 5 | 7 | 6 |
| my kid fell into the fire while we were making a fire | red | 1 F | 1 | 1 | 0 | 2 | 2 |
| treat water in the lungs after drowning | red | 5 F | 0 | 0 | 5 | 2 | 2 |
| how do i treat water blisters on a burn | yellow | 7 F | 8 F | 8 F | 7 F | 8 F | 8 F |
| how do i treat water poisoning | yellow | 8 F | 6 F | 6 F | 7 F | 7 F | 7 F |
| light a fire to keep him warm with hypothermia | red | 4 | 0 | 0 | 4 | 3 | 3 |
| my son nearly drowned in the rainwater pool | red | 2 | 2 | 2 | 5 F | 5 F | 5 F |
| someone fell in the rainwater pool and isn't breathing | red | 3 | 3 | 3 | 5 F | 5 F | 5 F |
| he swallowed pool water and now he's coughing | yellow | 1 | 1 | 1 | 4 | 4 | 5 |
| drank creek water and now i have diarrhea | yellow | 8 F | 8 F | 8 F | 8 F | 8 F | 8 F |
| my child swallowed lamp oil | red | 3 | 3 | 3 | 5 F | 5 F | 5 F |
| scorpion sting on my foot | yellow | 8 F | 8 F | 8 F | 8 F | 8 F | 8 F |
| rash from poison ivy | yellow | 8 F | 8 F | 8 F | 6 F | 6 F | 6 F |
| snake bite while camping | red | 8 F | 8 F | 8 F | 8 F | 8 F | 8 F |
| hypothermia after falling in cold water | red | 8 F | 8 F | 8 F | 8 F | 8 F | 8 F |
| someone got shocked by a wire in the flood water | red | 0 | 0 | 0 | 0 | 0 | 0 |
| is it safe to put water on a burn | yellow | 3 F | 3 F | 3 F | 5 F | 5 F | 5 F |
| i burned my hand on the camp stove | yellow | 3 F | 3 F | 4 F | 7 | 7 | 7 |
| how do i treat a burn from a campfire | yellow | 8 F | 8 F | 8 F | 8 F | 8 F | 8 F |
| how do i light a campfire | green | 0 F | 8 F | 8 F | 2 F | 6 F | 6 F |
| i need to start a fire but i have no matches and no gas | green | 2 | 7 F | 7 F | 5 F | 8 F | 7 F |
| how do i make the water safe to drink | green | 8 F | 8 F | 8 F | 7 F | 8 F | 8 F |
| how do i purify water from a creek | green | 0 | 1 | 1 | 5 F | 5 F | 5 F |
| how to make the water safe for a baby's formula | green | 5 F | 8 F | 8 F | 8 | 8 F | 8 F |
| make a fire escape plan for my family | green | 6 | 3 | 4 | 6 | 6 F | 6 F |
| what could make a fire spread faster | green | 3 F | 3 F | 4 | 6 | 6 | 5 F |
| pour water on a grease fire | red | 4 F | 4 F | 4 F | 5 F | 5 F | 7 F |
| how do i treat water damage on the floor | green | 0 | 8 | 8 | 3 | 4 | 5 |
| **Total of 256** | | **141** | **142** | **144** | **178** | **185** | **186** |
| Typo versions, total | | 101 | 91 | 152 | 143 | 142 | 183 |

- **Totals barely move** across versions on clean wording: 141 -> 142 -> 144 keyword-only, 178 -> 185 -> 186 hybrid.
  The totals hide trades: the forks win the how-to questions #128 was for (light a campfire 0 -> 8, start a fire 2 -> 7,
  formula 5 -> 8, water damage 0 -> 8) and lose the injury+phrase questions exactly as #154 predicted (water in the
  lungs after drowning 5 -> 0, hypothermia 4 -> 0, CO in a tent 8 -> 3, escape plan 6 -> 3/4).
- **Typos are where the new fork stands out:** 101 / 91 / **152** keyword-only, 143 / 142 / **183** hybrid. The new fork
  scores higher on the typo set than on the clean set in keyword-only (152 vs 144).

## 2. Triage scoring per colour

**clean** (first right / top-3 right / any useful in top 8 / every need covered; useful slots in brackets)

| | n | kw main | kw old | kw new | hy main | hy old | hy new |
|---|---|---|---|---|---|---|---|
| red | 13 | 7 / 12 / 12 / 10 (51) | 5 / 8 / 10 / 8 (35) | 5 / 8 / 10 / 8 (36) | 8 / 11 / 11 / 10 (63) | 8 / 10 / 12 / 11 (62) | 8 / 10 / 12 / 11 (63) |
| yellow | 11 | 9 / 10 / 10 / 10 (62) | 8 / 9 / 10 / 9 (59) | 8 / 9 / 10 / 9 (59) | 8 / 11 / 11 / 10 (71) | 8 / 11 / 11 / 11 (70) | 8 / 11 / 11 / 11 (70) |
| green | 8 | 4 / 5 / 7 / 7 (30) | 5 / 6 / 8 / 8 (40) | 4 / 6 / 8 / 8 (43) | 4 / 7 / 7 / 7 (42) | 6 / 7 / 7 / 7 (47) | 7 / 7 / 7 / 7 (46) |
| all | 32 | 20 / 27 / 29 / 27 (143) | 18 / 23 / 28 / 25 (134) | 17 / 23 / 28 / 25 (138) | 20 / 29 / 29 / 27 (176) | 22 / 28 / 30 / 29 (179) | 23 / 28 / 30 / 29 (179) |
| whole-book slots | | 50 in 16 q | 36 in 16 q | 16 in 9 q | 20 in 10 q | 27 in 14 q | 21 in 13 q |
| context > half the top 8 | | 2 | 6 | 8 | 1 | 2 | 2 |

**typo** (first right / top-3 right / any useful in top 8 / every need covered; useful slots in brackets)

| | n | kw main | kw old | kw new | hy main | hy old | hy new |
|---|---|---|---|---|---|---|---|
| red | 13 | 4 / 6 / 7 / 5 (27) | 3 / 4 / 7 / 5 (22) | 6 / 8 / 11 / 8 (43) | 5 / 10 / 12 / 8 (46) | 5 / 10 / 12 / 9 (45) | 7 / 10 / 12 / 10 (61) |
| yellow | 11 | 6 / 8 / 8 / 6 (43) | 5 / 6 / 6 / 6 (34) | 8 / 9 / 10 / 9 (61) | 7 / 9 / 10 / 9 (54) | 7 / 8 / 9 / 9 (51) | 9 / 11 / 11 / 11 (72) |
| green | 8 | 3 / 5 / 5 / 4 (23) | 3 / 4 / 4 / 3 (25) | 4 / 6 / 8 / 8 (42) | 2 / 6 / 8 / 8 (33) | 4 / 6 / 7 / 7 (36) | 6 / 7 / 7 / 7 (43) |
| all | 32 | 13 / 19 / 20 / 15 (93) | 11 / 14 / 17 / 14 (81) | 18 / 23 / 29 / 25 (146) | 14 / 25 / 30 / 25 (133) | 16 / 24 / 28 / 25 (132) | 22 / 28 / 30 / 28 (176) |
| whole-book slots | | 23 in 9 q | 13 in 7 q | 15 in 8 q | 16 in 9 q | 18 in 11 q | 16 in 10 q |
| context > half the top 8 | | 2 | 4 | 5 | 1 | 1 | 2 |

Keyword-only, clean, red (13): first right **7 main, 5 old fork, 5 new fork**; top-3 right **12, 8, 8**. That is the
#128-style phrase filter the fork carries (`36c7bd4`, guarded by `594fbaa` only for kitchen/building/accident and water
damage/heaters): no exception for burns, drowning, hypothermia or CO. Lost on both forks against main: "treat water in
the lungs after drowning" (first right, 5 useful -> none in top 3, 0 useful), "light a fire... hypothermia" (top-3 right
-> none), "my kid fell into the fire..." (first right -> none in top 3), "my clothes caught fire..." (top 3 -> none),
and yellow "i burnt my fingers lighting the campfire" (first right -> none in top 3). Hybrid hides most of it: red 8 / 8
/ 8 first right, 11 / 10 / 10 top 3.

Whole-book slots (title of a page over 20,000 characters, as `compare.py`): keyword-only 50 -> 36 -> **16**; hybrid 20 ->
27 -> 21. "Context over half the top 8" (pages about only the setting) rises in keyword-only on the forks, 2 -> 6 -> 8:
the fire-making and water-treatment pages the phrases pull in.

## 3. Typos (same 32, panicky spelling)

Clean -> typo, all 32:

| | kw main | kw old fork | kw new fork | hy main | hy old fork | hy new fork |
|---|---|---|---|---|---|---|
| first right | 20 -> 13 | 18 -> 11 | **17 -> 18** | 20 -> 14 | 22 -> 16 | **23 -> 22** |
| top-3 right | 27 -> 19 | 23 -> 14 | **23 -> 23** | 29 -> 25 | 28 -> 24 | **28 -> 28** |
| no useful page at all | 3 -> 12 | 4 -> 15 | **4 -> 3** | 3 -> 2 | 2 -> 4 | **2 -> 2** |

Old fork vs new fork, keyword-only typos: first right 11 vs 18, red 3 vs 6, #154 count 91 vs 152. Keyword-only, the new
fork loses the first page on 1 typo ("i burnt my hand on the camp stov") and gains it on 2; the old fork loses 9. What
the typo fix cannot help is a typo that is a real word: "my **sun** neary drowned" (hybrid 5 useful -> 1, first right ->
wrong, on the new fork too).

## 4. Confidence model on the new fork (committed coefficients, no refit)

| | kw clean | kw typo | kw all 64 | hy clean | hy typo | hy all 64 |
|---|---|---|---|---|---|---|
| first right (base) | 17/32 | 18/32 | 35/64 | 23/32 | 22/32 | 45/64 |
| top-3 right | 23/32 | 23/32 | 46/64 | 28/32 | 28/32 | 56/64 |
| AUC first right [95% bootstrap] | 0.773 [0.575-0.941] | 0.766 [0.569-0.933] | 0.771 [0.64-0.889] | 0.727 [0.498-0.917] | 0.7 [0.471-0.895] | 0.714 [0.563-0.847] |
| AUC top-3 right | 0.517 [0.283-0.748] | 0.589 [0.337-0.817] | 0.556 [0.391-0.71] | 0.54 [0.129-0.858] | 0.625 [0.138-0.967] | 0.585 [0.33-0.831] |
| Brier (base rate alone) | 0.199 (0.249) | 0.196 (0.246) | 0.198 (0.248) | 0.175 (0.202) | 0.191 (0.215) | 0.183 (0.209) |
| mean p | 0.534 | 0.561 | 0.547 | 0.741 | 0.72 | 0.73 |

For comparison, `CONFIDENCE.md` (362 questions): grouped-CV AUC first right **0.78** keyword / **0.74** hybrid
(in-sample 0.80 / 0.79); same model against top-3 right **0.737** / **0.756**.

Stored out-of-fold probabilities (grouped CV, the 29 overlapping questions, labels from this run): AUC first right
keyword **0.771** [0.57-0.95], hybrid **0.667** [0.44-0.88]; the committed coefficients on the same 29 give 0.790 /
0.717, so about 0.02-0.05 of the committed AUC here comes from these questions having been in the fit.

Calibration (n, mean p, first right, top-3 right):

| band | kw clean | kw typo | hy clean | hy typo |
|---|---|---|---|---|
| 0.00-0.25 | 4, 0.2, 0, 3 | 3, 0.19, 0, 2 | 0 | 0 |
| 0.25-0.50 | 10, 0.38, 3, 6 | 9, 0.38, 3, 5 | 2, 0.42, 1, 2 | 7, 0.43, 3, 5 |
| 0.50-0.75 | 13, 0.62, 10, 10 | 13, 0.6, 9, 10 | 15, 0.64, 8, 12 | 10, 0.66, 6, 9 |
| 0.75-1.00 | 5, 0.88, 4, 4 | 7, 0.88, 6, 6 | 15, 0.89, 14, 14 | 15, 0.89, 13, 14 |

Small n: bands of 2-15 questions; one question moves a band by 7-50 points.

Policy:

| | kw clean | kw typo | hy clean | hy typo |
|---|---|---|---|---|
| sure | 13 | 13 | 25 | 23 |
| buttons | 15 | 16 | 7 | 9 |
| reply+pages | 4 | 3 | 0 | 0 |
| buttons (compact) | 0 | 0 | 0 | 0 |
| reply, pages hidden | 0 | 0 | 0 | 0 |
| first right but buttons/reply | 7 | 8 | 4 | 4 |
| top-3 right but "help me help you" | 3 | 2 | 0 | 0 |
| none of top 3 right, no buttons | 3 | 3 | 3 | 2 |
| first wrong, no buttons | 3 | 3 | 6 | 5 |
| red/yellow with pages hidden | 0 | 0 | 0 | 0 |

(Urgent: buttons < 0.60, "help me help you" with pages < 0.25. Everyday: compact buttons < 0.30, reply with pages hidden
< 0.25.)

**How `urgent()` / `is_danger` classified them:** red 13 of 13, yellow 11 of 11, green 4 of 8 ("start a fire... no gas",
"formula" (baby), "escape plan", "fire spread" are urgent by the wide list: harmless, it only keeps pages). The narrow
`assistant.DANGER` sign fires on 4 (clothes on fire; water in the lungs after drowning, as "stuck in water"; water
poisoning; snake bite). **Urgent questions that lost their pages: 0** (both modes, clean and typo). The 4 everyday
questions (light a campfire, water safe to drink, purify water from a creek, water damage) all had p >= 0.68, so the
everyday 0.30 cut never fired: no compact buttons, no hidden pages.

The confident misses (no buttons, nothing right in the top 3):
- keyword: **treat water in the lungs after drowning** (red, p 0.73: top 3 are an emergency drinking-water note and two
  wastewater manuals), how do i purify water from a creek (green, 0.68, wastewater manual first), how do i treat water
  damage on the floor (green, 0.96, flood glossary).
- hybrid: **light a fire to keep him warm with hypothermia** (red, 0.66, cold-weather and survival manuals on making
  fire), **someone got shocked by a wire in the flood water** (red, 0.71, flood booklets), water damage (0.97).

Why the phrase cases fool it: the phrase's groups count toward coverage. "treat water in the lungs after drowning" is
searched as [water] [disinfect/treatment/chlorine...] [lungs] [after] [drowning]; a wastewater page covers 3 of 5 groups
(`cover1` 0.6, `title1` 0.4), so the model reads a hijacked search as a good one.

## 5. Against the in-sample numbers: what holds and what doesn't

Holds (with wide error bars):
- **First-page AUC:** 0.77 keyword / 0.73 hybrid on the clean 32, 0.77 / 0.70 on the new typo text, against 0.78 / 0.74
  in CV. Bootstrap intervals run from about 0.5-0.6 to 0.9-0.94, so this says "not obviously worse", not "the same".
- **Keyword-only calibration** points the right way: 0 of 4 first right below 0.25, 3 of 10 at 0.25-0.50, 10 of 13 at
  0.50-0.75, 4 of 5 above 0.75 (predicted 0.20 / 0.38 / 0.62 / 0.88). Brier 0.199 vs 0.249 for the base rate.
- **Safety rule:** every red and yellow question is `urgent`; no pages hidden. The everyday cut stays quiet (0 of 4).
- **Hybrid action mix:** 25 sure / 7 buttons / 0 reply (78 / 22 / 0 %); in-sample 82 / 18 / 0 %. Keyword-only 13 / 15 /
  4 (41 / 47 / 12 %); in-sample 50 / 43 / 7 %.
- **New-fork search on typos:** typos cost the new fork nothing here (keyword first right 17 -> 18), against -7 for main
  and old fork. In-sample (`COMPARE_rewrite.md`) typo useful-in-top-8 went 2.23 -> 4.72 keyword; here useful slots on
  typos 81 (old fork) -> 146 (new fork).

Does not hold, or is worse:
- **Top-3 rightness: no signal.** AUC 0.52 keyword / 0.54 hybrid (typos 0.59 / 0.63) vs 0.74 / 0.76 in-sample. Only 9
  (keyword) and 4 (hybrid) of 32 clean questions have nothing right in the top 3, so this is weak evidence either way,
  but nothing here supports reading the first-page probability as "one of the first 3 is right".
- **Confident misses are more frequent:** nothing right in the top 3 and no buttons on 3 of 32 in each mode (9 %),
  against 14 of 362 (4 %) keyword and 21 of 362 (6 %) hybrid in-sample. One of the keyword three and two of the hybrid
  three are red. Three events are not a measured rate, but this is the failure the model exists to catch, and these are
  the phrase-collision questions this set was written to show.
- **More buttons on right answers in keyword-only:** 7 of 17 first-right questions get buttons or the reply (41 %;
  in-sample 70 of 216 = 32 %). Hybrid 4 of 23 (17 %; in-sample 35 of 276 = 13 %).
- **"Help me help you" while a right page was at 2 or 3 (keyword):** 3 of the 4 keyword reply cases (son nearly drowned,
  fell in the pool and isn't breathing, fire spread faster). Pages are still shown (urgent), so the cost is the wording,
  not lost pages.
- **Hybrid calibration at 0.50-0.75:** 8 of 15 first right against 0.64 predicted.
- **Keyword-only search on red injury+phrase questions is worse on the forks than on upstream main** (first right 7 -> 5,
  top 3 12 -> 8, of 13). The in-sample `COMPARE_rewrite.md` showed red flat (44 % -> 44 %, base = fork before the
  rewrite); on this subset, which is mostly phrase collisions, both forks lose against main. Hybrid does not show it.

## Most telling questions

1. **treat water in the lungs after drowning** (red). Main keyword-only: Basic Emergency Care first, 5 of 8 useful. Both
   forks keyword-only: 0 of 8, wastewater and chlorination manuals, and the new fork is *sure* (p 0.73); the narrow
   danger sign ("stuck in water") fires but the water phrase is still applied. Hybrid: resuscitation pages at 2-3, p 0.67.
2. **someone got shocked by a wire in the flood water** (red): 0 of 8 on all six runs; hybrid sure at 0.71. A gap in what
   the search reaches, not ranking, and the confidence model does not see it.
3. **light a fire to keep him warm with hypothermia** (red): main 4 useful, top 3 right; forks 0 (keyword) / 3 (hybrid)
   with fire-making pages on top. Keyword gets buttons (0.40); hybrid is sure (0.66) with nothing right in the top 3.
4. **my son nearly drowned in the rainwater pool / someone fell in the rainwater pool and isn't breathing** (red,
   keyword-only): first page wrong but a resuscitation page at 2-3; p 0.21 / 0.17, so the "help me help you" reply with
   pages. Right to doubt the first page; the reply then talks as if nothing fits when a page at 2-3 does.
5. **how do i light a campfire / start a fire without matches** (green): the trade that justifies the phrases. Main
   keyword-only 0 and 2 of 8, both forks 8 and 7, sure at 0.91 / 0.67.

## Anything broken

- Nothing crashed. All six runs completed (keyword 3-8 s, hybrid 48-89 s); the semantic index loaded (337,016) in every
  hybrid run; `turn_hits` and the traced `hybrid` returned the same pages for all 64 queries on the new fork.
- Known hole re-confirmed: the fork's fire/water phrases have no injury exception (#154's own point); `594fbaa` guards
  only kitchen/building/accident and water damage/heaters. A narrow DANGER sign in the question does not switch the
  phrase off either.
- The confidence model counts phrase groups as coverage, so a phrase that hijacks a search raises confidence instead of
  lowering it.
