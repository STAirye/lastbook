# Lessons from #128, #154 and #241 (2026-11-18)

GitHub read-only (`gh pr view`, `gh issue view`, `gh api` GETs). Nothing posted, nothing committed, no servers.
Numbers: `LESSONS_154.json` (made by `analyze_sets.py` from `r128/*.json`, made by `run_sets.py`).

Code and data:

| Name | Code | Data |
|---|---|---|
| main | `origin/main` 4fd221e (1.1.12), worktree `.claude/worktrees/lessons-main` (detached) | `D:\LastbookData` |
| 1f31f2a | fork tip with 1.1.12 merged, worktree `.claude/worktrees/lessons-1f31f2a` (detached) | (only #241's tests: no data) |
| new | `fork/phrase-injury` fe635e7 (newest fork code, without 1.1.12), worktree `phrase-injury` for searches; detached copy `lessons-new` + #241's two test files (untracked) for the tests | `D:\LastbookData-fork-test` |

Searches in-process and read-only as `conf_eval.py` (sections build refused, read-only connections, vector file never
truncated, no model), `python -B -X utf8`. Keyword-only = `retrieval.AVAILABLE=False` (`TH_KW=1`), as the desktop app
ships. As in RESULTS_154, main and the fork run on different data folders (the fork's has the section rows).

## 1. #128's questions in the triage set (`cases128.py`)

**Sources.** #128's unit test (`SearchWords`), its review (wonderdawg named two breakages: "how do i prevent a generator
from starting a fire" went to a wilderness fire-starting handbook; "how do i treat water intoxication" got the drinking-water
rewrite), its body and #126 (`check_search_fire.py`'s 3 questions, the "fire tinder" reference search, and the 20 everyday
prompts with 4 controls, which are `tools/fork_search_check.py`'s list). The owner's other recent PR, #170 (UTF-8 in
`test_chat_steps`, merged), has no questions; #128 is his only closed one.

**Added:** 21 topics, 27 clean questions (7 counterexamples) + 25 typos, labelled blind (colour, need, not_first, typo)
before any run. 8 new need keys (water intoxication, going back inside, north without a compass, cooking without power,
infant feeding, emergency news, toilet paper, flushing).

**Left out as duplicates of `cases.py`:** "how do i light a campfire" (108.0), "i need to start a fire but i have no matches
and no gas" (108.1) and its "..., how do i do it" form, "how do i purify water from a creek" (101.0), "how do i make the
water safe" (~ "...to drink"), the bare stems "make the water safe" and "purify water". The test's short "there is a building
fire next door" and "the fire started in the kitchen" are kept once, in their longer fork_search_check wording. Not added:
#128's end-to-end follow-up turn (a conversation).

**Results** (first result right / useful pages in top 8, summed):

| | keyword main | keyword new | hybrid main | hybrid new |
|---|---|---|---|---|
| clean, 27 | 16 / 120 | **18 / 142** | 24 / 160 | 23 / 167 |
| typos, 25 | 13 / 90 | **15 / 114** | 15 / 118 | **20 / 146** |
| green how-to, 17 | 11 | 14 | 15 | 16 |
| counterexamples, 7 | 3 | **2** | 6 | **5** |
| wrong-sense first page (clean + typo) | 2 | **4** | 2 | 2 |

- **Gains (keyword):** "how to start a fire", "make fire", "make fier" (0 -> 1, 0 -> 8 useful), "no fuel to boil water...",
  typo'd bleach, "bleding", "insulen". The fire/water phrases and typo correction do what #128 wanted.
- **Our fork still has both breakages #128's reviewer named**, plus #154's escape-plan one:
  - "how do i prevent a generator from starting a fire" (keyword): first page ATP 3-50.21 / USMC fire-making, not the
    Honda generator manual. The phrase fires on "starting a fire"; the fork's `unless` lists kitchen/building/spread...,
    not "prevent". main: generator page first.
  - "how do i treat water intoxication" (keyword and hybrid): wastewater and disinfection manuals. INJURY has no
    "intoxication". Hybrid main got it right (1 -> 0).
  - "make a fire escape plan for my family" (keyword, all four sets that have it): ATP 3-50.21 first, "make a fire" matches.
- **Other misses, all versions:** "how to strat a fire" and "he has no puls" ("strat", "puls" are library words, so typo
  correction leaves them; "sope" becomes "scope"); "he has no pulse" keyword: First Aid p.7 ("If there is no pulse, see No
  Heartbeat") is first but CPR's pattern has no pulse/heartbeat, so it scores 0 (a label-pattern gap, left as labelled).
  "the pump is not responding" keyword: a computer-science book first on both.

**Fix tried (scratch, not committed):** widen the two phrases' `unless` - fire: prevent, avoid, stop, risk, hazard, cause,
escape, spread, safety, drill; water: intoxication, poisoning, lungs, overdose. On all 499 questions of `cases.py`,
`cases154.py`, `cases128.py`, `cases241.py`, keyword-only: only the target questions move (generator clean + typo 0 -> 1
first right; escape plan x4: firecraft gone, 4 -> 6-8 useful; water intoxication: wastewater manuals gone), first right
304 -> 306, useful 2433 -> 2445, nothing lost. Hybrid (same 499): only the same questions move, first right 380 -> 378,
useful 2868 -> 2872: water intoxication 0 -> 1 (clean and typo; "Food and Water in an Emergency" instead of engineering
manuals), generator stays right (Honda manual first now), but the escape plan x4 goes 1 -> 0 ("Mult-Family Home escape
routes" -> "Make A Plan", which the ESCAPE pattern does not match: a family-plan page, arguably fine). So: clear win
keyword-only, mixed by the strict scorer on hybrid. Script: `patch_guard_check.py`; outputs `r128/patch_guard_{kw,hy}.txt`.

## 2. #154, #167, #241: what upstream checks and what the maintainers said

**#241** (gudekarN, merged 093b8d3 into 1.1.12): `app/tests/test_topic_search_emergency.py` + `topic_search_emergency.mjs`.

- **What it searches: the guides, not the library.** Each question runs through `web/words.js` `rankTopics` over
  `content/topics/*.json` (the app's guide search, via Node), with app.js's stop words. No data folder; `server.find` and
  `assistant._fts` (what #154 is about, and all our work) are explicitly not covered. Its docstring says it lets "a change
  to the phrase handling in `server.PHRASES`" be measured; it cannot: PHRASES is not in the guide search.
- **Questions:** 9 emergency (drowning x3, burns x4, lamp oil, CO in a tent; from #154's table, with "isn't" spelled
  "is not") and 12 counterexamples (#167's left-out words: "not responding to antibiotics", "the pump is not responding",
  "choking on smoke", "allergic reaction choking"; how-to: light a campfire, start a fire, boil water, escape plan, fire
  spread; "trouble breathing", "someone fainted", "food went bad").
- **Expected and scored:** each emergency question has the (guide, choice) that should lead. Score 1.0 guide + choice,
  0.5 right guide, 0 another guide. `BASE_FIRST` records what main (9542e80) gives for all 21; `KNOWN_GAPS` the 7
  emergency ones that score < 1 (emergency score today 3.0 of 9).
- **What counts as pass** (5 tests): baseline reproduced exactly; scorer; gaps only shrink; no emergency question below
  its baseline; **counterexamples do not move at all** (equality with `BASE_FIRST`). Any change of a recorded first result
  fails `test_reproduces_the_baseline` on purpose: the PR must re-record the baseline and say so.
- Two counterexample baselines are themselves wrong and are now frozen: "the pump is not responding" -> hurt / Not
  breathing ("breathing is a keyword match"), and "how do i light a campfire" -> Power / first hours. A fix that sends the
  pump question anywhere else fails the test.

**How their framing differs from ours**

| | #241 | ours (`cases*.py`, `score.py`, `engine/confidence.py`) |
|---|---|---|
| Searched | guides (words.js) | library pages (`/api/retrieve`, `assistant.hybrid`), keyword and hybrid |
| Truth | one (guide, choice) per question | patterns for what a useful page says, most urgent first; context; not_first |
| Measure | first result only, 0 / 0.5 / 1 | first right, top 3, useful of 8, coverage of 2 needs, context share, wrong sense |
| Urgency | emergency vs counterexample (two lists) | red / yellow / green per question |
| Counterexamples | 12, must not move at all | 22 + 7 + 12, first page must not be the wrong sense (may improve) |
| Typos, conversations | none | 109 + 25 typos, 52 conversations |
| Confidence | none | logistic model, buttons / ask to say more |
| Baseline | a commit, exact first results, re-recorded on purpose | main vs fork aggregate numbers |
| Size | 21 questions, runs in 0.07 s, no data | 499 questions, needs a data pack |

What to take from theirs: exact recorded baselines that fail loudly and must be re-recorded in the PR that changes them;
a baseline commit hash; counterexamples that guard ordinary searches; no data needed, so it runs in CI.

**Maintainer direction** (wonderdawg; #154, #241, #128, #44):

- "#167's `urgent` field is the existing integration point; there is no need to build a competing emergency-rule
  mechanism. Maintainers will own combining it with #44, #158 and #183 and checking the shared phrase source." (#154).
  #167 (open) has 5 phrases on one choice; our fork has `assistant.DANGER`, `engine/confidence.URGENT` (~100 words) and
  `INJURY`: exactly the competing mechanism, three times.
- They asked for a "focused test-only PR" with questions, expected first results, scorer, the non-emergency
  counterexamples and the baseline commit; "a small fixture plus a documented command is enough". #241 did that, for the
  guides. "The counterexamples are the part we valued most ... a future fix for #154 can't quietly improve injury questions
  by breaking ordinary searches."
- #154 stays open "until a retrieval change is verified against them"; when guide changes land (#44) the two burn rows
  will improve and "the baseline will be re-recorded in that change".
- #128: narrow the phrases; "a small test that pairs each positive example with its safety or medical counterpart and
  checks that the latter keeps its existing search terms", in `SearchWords`. #44: regression cases asserting topic and
  choice, in both word-splitting modes.
- Invented situations only; no personal records.

## 3. #241's tests on three versions

`python -B -X utf8 -m unittest app.tests.test_topic_search_emergency -v` and the report mode, Node 26.13.1:

| | origin/main 4fd221e | fork 1f31f2a | new (phrase-injury + the two files) |
|---|---|---|---|
| 5 tests | pass | pass | pass |
| emergency score | 3.0 of 9 | 3.0 of 9 | 3.0 of 9 |
| counterexamples moved | 0 | 0 | 0 |

All 21 first results are identical. **Why:** the tests run `web/words.js` over `content/topics`; every fork search change
is in `server.py`, `assistant.py` and `engine/` (document search) or the chat UI. 1f31f2a has upstream's guides as is.
phrase-injury predates 1.1.12 and lacks some upstream guide edits (power, sanitation, shelter), but none of them moves
these 21. So our changes neither break nor fix anything #241 can see, and #241 cannot see #154's actual failure.

## 4. #241's questions through our scorer and confidence model (`cases241.py`)

Labelled blind for pages (colour, need, not_first). Agreement with our earlier labels on the 12 shared questions: colour
12 of 12, first need 10 of 12 (pool not-breathing: CPR vs DROWN first; fire spread: FIRESPREAD vs ESCAPE).

| first right / useful | keyword main | keyword new | hybrid main | hybrid new |
|---|---|---|---|---|
| all 21 | 12 / 101 | 12 / 113 | 14 / 121 | **17** / 120 |
| 9 emergency | 5 / 39 | 5 / 41 | 5 / 50 | 5 / 48 |
| 12 counterexamples | 7 / 62 | 7 / 72 | 9 / 71 | **12** / 72 |

- Emergency questions still 5 of 9 first right everywhere. Wrong first in all versions: "burned my hand trying to light a
  fire" (trail notebook keyword; "How to start a fire" hybrid), "my clothes caught fire while starting the fire", "my son
  nearly drowned in the rainwater pool" (keyword), "my child swallowed lamp oil" (keyword); hybrid also "treat water in the
  lungs after drowning" and "i burned my hand on the camp stove". The fork's injury rule keeps the phrase off, but the
  setting words still outvote the injury: #154's proposal 3 (document tiers for emergency questions) is the missing part.
- Counterexamples: hybrid new fixes escape plan, fire spread, food went bad; keyword new gains "how do i start a fire" but
  "make a fire escape plan" goes to firecraft (above).

**Confidence (new, committed coefficients, chat's first search):**

| | n | first right | AUC first | Brier (base rate) |
|---|---|---|---|---|
| cases241 keyword | 21 | 12 | 0.93 | 0.124 (0.245) |
| cases241 hybrid | 21 | 17 | 0.85 | 0.126 (0.154) |
| cases128 keyword | 52 | 33 | **0.67** | **0.232 (0.232)** |
| cases128 hybrid | 52 | 43 | 0.79 | 0.124 (0.143) |

- On #241's set the model ranks well (tiny n). On #128's everyday set keyword-only it is **no better than the base rate**
  (out-of-sample, against 0.78 cross-validated on cases.py).
- Sure but wrong (keyword): "how do i put out a fire" 0.96 (Outdoor Fire Safety: arguably right, label), "how to strat a
  fire" 0.93 (a strategic plan), "no internet... emergency news" 0.77, "he has no pulse" 0.68, **"how do i treat water
  intoxication" 0.66**: the phrase injected disinfect/treatment, the wastewater pages carry those words, and the coverage
  signal counts them as the question's own. A wrong rewrite looks confident.
- **Urgency is too wide for the everyday rule:** `is_danger` is true for 17 of 38 green #128 cases (fire, gas, dead,
  baby, emergency, bleach, generator), so the 0.30 everyday cut seldom applies: cooking without power (0.48), baby formula
  (0.37), dead car battery (0.55) and the generator question (0.48) get the emergency buttons. On #241's set: "how do i
  start a fire", escape plan, fire spread are urgent.
- **And narrow where it matters:** "he has no puls what do i do" (red) is not urgent (typo not corrected), p 0.22 ->
  everyday "unsure": the chat gives no answer, only the ask-to-say-more text (UNSURE_TEXT; pages as consulted, none
  cited), for someone without a pulse. The clean "he has no pulse" is urgent and fine.

## 5. What to change, ranked

**Our code (fork)**

1. Widen the fire/water phrase `unless` (prevent/avoid/risk/cause/escape/spread/safety/drill; intoxication/poisoning/
   lungs/overdose): fixes both #128-review breakages and the escape plan keyword-only, nothing lost on 499 questions; hybrid: intoxication fixed, escape plan scored 1 -> 0 (a family-plan page instead of escape routes).
   Then add #128's pairs as `SearchWords` tests (positive and its counterpart), as the reviewer asked.
2. Never withhold the answer when the question names a body sign, typo or not: match near-misses of the urgent words
   ("puls", "breating") even when typo correction keeps them as library words, or let the everyday rule offer buttons
   only, never the "say more" reply.
3. Confidence: compute coverage on the person's own words, not on words a phrase injected (or as a separate signal); refit
   with cases128 + cases241 added, grouped by topic.
4. Narrow is_danger for the button cut (fire as making, gas as fuel, dead battery, baby formula) - and longer term take it
   from #167's `urgent` phrases, as the maintainers want.
5. Typo correction: real-word errors ("strat", "puls", "sope" -> "scope") need a context check (keep a library word only
   if it fits the other words; prefer emergency vocabulary).
6. Emergency questions whose setting outvotes the injury (burns at a fire, drowning in a pool, lamp oil): #154's
   document tiers are still undone; that is where 4 of 9 #241 questions fail on pages.

**Our test set**

1. Keep `cases128.py` and `cases241.py` in the set (done); refit and re-score with them.
2. Add a recorded-baseline mode, as #241: per question the exact first page (doc, page) on a named main commit, failing
   loudly when it moves.
3. Add the CPR pattern's missing "pulse|heartbeat" (and check other patterns against pages that are right but scored 0)
   - separately from the blind labels, and re-score all sets.
4. More real-word typos and counterexamples of the "prevent X from starting a fire" kind (cause, risk, avoid).
5. Write a guide-level column for our red questions, so the same question is scored on guides (as #241) and pages.

**The upstream draft summary (`upstream-triage-summary.md`)**

1. Step 1 ("the test-only PR asked for on #154") is done, by #241, for the guides. Reword: ours would be the
   document-search complement (what #154 measured: `server.find` / `assistant._fts`), which #241 says it does not cover.
2. Baseline `256d52f` -> current main 4fd221e, re-measured; record it as #241 does.
3. Say plainly that the fork's urgency lists (DANGER, URGENT, INJURY) are not proposed upstream; only #167's `urgent`
   phrases. Drop wording that reads like a rule mechanism; offer the measurements.
4. #128 is closed; say its two review counterexamples (generator, water intoxication) and the escape plan are in our set
   and what fixes them, so a future phrase PR starts from those pairs.
5. Mention #241's two frozen wrong baselines (pump -> Not breathing; campfire -> Power) as a question, not a fix.
6. Lead with the counterexamples (they "valued most"), and with keyword-only numbers: the desktop app ships that way.
