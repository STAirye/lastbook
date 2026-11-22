# Search confidence: is the first page right? (2026-11-18)

Predict at search time, with no language model, how likely the first result is right, and let the chat act on it:
below 75 % offer buttons, below 25 % ask the person to say more. Code: branch `fork/search-confidence`
(worktree `.claude/worktrees/search-confidence`), `engine/confidence.py`.

## How it was measured

- **Questions:** `cases.py`, 362 invented questions (253 clean, 22 counterexamples, 109 typos) over 159 topics.
  Labels from `score.py`: `first_ok` (target), and "a useful page in the top 8" (useful > 0).
- **Searches:** `conf_eval.py`, in-process, `assistant.hybrid(q, 8, trace=...)` as `/api/retrieve` and the chat's first
  search do it. Read-only on `D:\LastbookData-fork-test` (sections build refused, read-only index connections, vector file
  never truncated). Keyword-only = `retrieval.AVAILABLE=False` (`TH_KW=1`), as the desktop app ships. Output
  `conf_kw.json`, `conf_hy.json` (each question's hits, trace, signals and labels; and the 52 conversations).
- **Hook:** `assistant.hybrid` and `_fts` take an optional `trace` dict and fill it with the word groups, rows with every
  word, the any-word fallback, each keyword row's bm25, and (hybrid) each passage's cosine and both searches' top-8 keys.
  No change to results.
- **Fit:** `conf_fit.py` (all candidate signals, single-signal AUC, greedy selection), `conf_final.py` (final sets):
  standardised L2 logistic regression (C = 0.3), **grouped cross-validation by topic** (a topic's clean and typo
  questions in the same fold), 5 folds x 20 shuffles. All numbers below are out-of-fold unless marked in-sample.
  Coefficients are then refitted on everything and written back on the raw signals as plain numbers.
  `conf_policy.py` checks that `engine/confidence.py` reproduces the fit (max |dp| 0.0005) and simulates the chat.

## Signals

Candidates tried (single-signal AUC for first right, keyword / hybrid): coverage of the question's word groups in the
first page's title+excerpt `cover1` .74/.66; all groups present `all1` .66/.62; coverage in the first title `title1`
.59/.58; first bm25 / sum of the groups' IDF `kw_top_per_idf` .72/.65; raw bm25 .64/.56; gap to #2 .52/.58; NQC-style
spread .55/.54; rows with every word `strict` .66/.65; any-word fallback .61/.60; number of groups .65/.63; mean and max
IDF; words not in the library after typo fix (always 0 once corrected, dropped); fewer than 8 hits; distinct documents
`docs` .56/.62; emergency book in top 8 .55/.52; first page from an emergency book `emerg1` .58/.54; danger sign;
best cosine `cos1` .70; cosine drop to #8; keyword/vector top-8 overlap `overlap` .64; first page found by both .53.

Final sets (standardised weight, i.e. per standard deviation; + = more likely right):

| Keyword-only | | Hybrid | |
|---|---|---|---|
| cover1 | +0.71 | all1 | +0.58 |
| title1 | +0.51 | cos1 | +0.47 |
| kw_top_per_idf | +0.49 | title1 | +0.38 |
| emerg1 | +0.40 | docs | -0.37 |
| idf_mean | +0.27 | strict | +0.33 |
| strict | +0.09 | emerg1 | +0.26 |
| | | cos_drop | -0.22 |
| | | overlap | +0.20 |

In words: the best single sign is whether the first page actually carries the question's words (or synonyms); then
how strongly keyword search matched relative to how rare the words are; with vectors, the best cosine and agreement
between the two searches. The whole-book / long-page signal no longer matters since sections (3k).

## Accuracy

| | Keyword-only | Hybrid |
|---|---|---|
| First result right (base rate) | 60 % | 76 % |
| Grouped-CV AUC, first right | **0.78** (sd 0.008) | **0.74** (sd 0.016) |
| red only / clean / typos | 0.75 / 0.77 / 0.80 | 0.70 / 0.76 / 0.70 |
| Same model vs "a useful page in top 8" | 0.72 | 0.82 |
| In-sample AUC (overstates) | 0.80 | 0.79 |
| Brier (base rate alone) | 0.187 (0.241) | 0.158 (0.181) |
| Cost per estimate | ~1.4 ms | ~1.4 ms |

Calibration, out-of-fold (band: n, mean predicted, actual first right):

| Band | Keyword-only | Hybrid |
|---|---|---|
| 0-25 % | 25, 0.21, 0.20 | 1, 0.23, 1.00 |
| 25-50 % | 107, 0.37, 0.36 | 26, 0.41, 0.46 |
| 50-75 % | 113, 0.62, 0.65 | 139, 0.65, 0.62 |
| 75-100 % | 117, 0.87, 0.85 | 196, 0.89, 0.90 |

Well calibrated in bands. Hybrid predictions are squeezed into 0.23-1.0: hybrid search is rarely bad enough for 25 %.

## Threshold tables (out-of-fold)

Columns: share of questions below the cut; questions whose first page WAS right but fall below (false alarms); wrong
ones at or above (slips); with a useful page but below; red questions (counterexamples out, typos in) below / right but
below / wrong at or above; questions with an `assistant.DANGER` sign, right but below.

**Keyword-only** (216 right, 146 wrong, 218 red of which 106 right)

| cut | below | false alarms | slips | useful>0 below | red below | red right below | red wrong above | danger right below |
|---|---|---|---|---|---|---|---|---|
| 0.15 | 3 (1%) | 0 | 143 | 1 | 3 | 0 | 109 | 0 of 46 |
| 0.20 | 9 (2%) | 1 | 138 | 6 | 8 | 0 | 104 | 1 |
| **0.25** | 25 (7%) | **5** | 126 | 15 | 21 | **3** | 94 | 1 |
| 0.30 | 45 (12%) | 11 | 112 | 31 | 36 | 6 | 82 | 2 |
| 0.40 | 96 (27%) | 29 | 79 | 69 | 75 | 19 | 56 | 7 |
| 0.50 | 132 (36%) | 43 | 57 | 95 | 98 | 28 | 42 | 11 |
| 0.60 | 182 (50%) | 70 | 34 | 135 | 129 | 41 | 24 | 17 |
| 0.70 | 225 (62%) | 103 | 24 | 173 | 146 | 54 | 20 | 27 |
| **0.75** | 245 (68%) | 116 | **17** | 191 | 155 | 59 | **16** | 27 |
| 0.80 | 272 (75%) | 137 | 11 | 215 | 169 | 67 | 10 | 30 |

**Hybrid** (276 right, 86 wrong, 218 red of which 156 right)

| cut | below | false alarms | slips | useful>0 below | red below | red right below | red wrong above | danger right below |
|---|---|---|---|---|---|---|---|---|
| **0.25** | 1 (0%) | **1** | 86 | 1 | 1 | **1** | 62 | 0 of 64 |
| 0.30 | 3 (1%) | 2 | 85 | 3 | 3 | 2 | 61 | 0 |
| 0.40 | 11 (3%) | 5 | 80 | 10 | 10 | 4 | 56 | 2 |
| 0.50 | 27 (7%) | 13 | 72 | 24 | 24 | 11 | 49 | 3 |
| 0.60 | 66 (18%) | 35 | 55 | 58 | 53 | 27 | 36 | 8 |
| 0.70 | 119 (33%) | 69 | 36 | 110 | 89 | 52 | 25 | 18 |
| **0.75** | 166 (46%) | 99 | **19** | 154 | 122 | 74 | **14** | 25 |
| 0.80 | 198 (55%) | 127 | 15 | 185 | 142 | 91 | 11 | 33 |

## The red rule: danger signs are too narrow, so a wide "may be urgent" list

The lowest-confidence questions are mostly red ones, and most of them have **no** `assistant.DANGER` sign: only 81 of
218 red questions match it ("my son isn't breathing", "fell off the roof can't move legs", "her face is drooping"
don't). Holding pages back on those would be the worst error. So the safety rule uses `assistant.is_danger`: a DANGER
sign, a danger button, or a word of the wide `confidence.URGENT` list (breathing, bleeding, fell, face, chest, smoke,
pills, baby, cut, car, help, ...), on the question as typed and as typo-corrected, and on the message it is joined with.
It matches 218 of 218 red questions, 49 of 72 yellow, 26 of 50 green, 18 of 22 counterexamples; of the 41 red
conversations, 33 by their last message alone ("what should i not do" is not) and 41 by some message, which is why
`turn_hits` also checks the message it joins with. A match costs nothing but showing pages. It was
written alongside this test set, so recall on new wording will be lower than 100 %.

## What the chat does with 75 / 25 (simulated, `conf_policy.py`)

| Keyword-only | questions | first right | a useful page | red (first right) |
|---|---|---|---|---|
| Answer as before (>= 75 %) | 117 (32 %) | 100 | 112 | 63 (47) |
| Buttons + answer (25-75 %) | 220 (61 %) | 111 | 176 | 134 (56) |
| "Help me help you" + pages (urgent, < 25 %) | 25 (7 %) | 5 | 15 | 21 (3) |
| "Help me help you", pages only under "Also looked at" | 0 | | | |

| Hybrid | questions | first right | a useful page | red (first right) |
|---|---|---|---|---|
| Answer as before | 196 (54 %) | 177 | 195 | 96 (82) |
| Buttons + answer | 165 (46 %) | 98 | 153 | 121 (73) |
| "Help me help you" + pages | 1 (0 %) | 1 | 1 | 1 (1) |

The test set is emergency-heavy, so almost every unsure question counts as possibly urgent; on everyday questions the
"pages only under Also looked at" row would fill instead.

**Conversations** (52, last message, committed coefficients, the better of the message's own search and the joined
one): confidence says little here. Keyword-only: 14 above 75 % (6 right), 35 in buttons (20 right), 3 below 25 % (2
right). Hybrid: 36 above (27 right), 16 in buttons (6 right), none below. In a follow-up the first page is often one the
previous answer cited, which no search score describes. So inside a conversation (routes follow / correct) the chat
only offers buttons, never the "help me help you" reply; that reply is for a new question (route first) or a new
danger sign (route danger, always with pages).

## Recommendation

- **Keep 75 / 25 as the defaults** (they are what was asked, and the probabilities are calibrated, so they mean the
  same in both modes). At 25 % keyword-only: 7 % of questions, 5 of 216 right ones caught (3 red), and every one of
  those red ones still gets its pages.
- **Buttons at 75 % are frequent in keyword-only mode: 68 % of questions** (46 % hybrid). If that feels like nagging,
  `LASTBOOK_CONF_BUTTONS=0.6` halves the false alarms (116 -> 70) for twice the slips (17 -> 34), with buttons on 50 %.
- **Hybrid almost never goes below 25 %.** For the "help me help you" reply to appear about as often as keyword-only's,
  hybrid would need ~0.45 (between 3 % and 7 % of questions, 5-13 false alarms). Not done: thresholds are one pair for
  both modes.

## Caveats

- 362 questions written alongside the search code; topics are grouped, but they are still one person's wording. AUC
  0.74-0.78 is a useful but rough signal: 15 % of "sure" keyword-only answers still start on a wrong page.
- `first_ok` is a regex label on title+excerpt; several "wrong but sure" cases are first-aid pages the regex misses.
- `/api/find` (Guides search, grouped by document) does not get a confidence; `/api/retrieve` and the chat do.
- The buttons and the reply were checked by unit tests and the event stream, not in a browser.

## Buttons at 0.60, and "first page right" vs "one of the first 3 right" (2026-11-18, later)

Decided by <owner>: buttons default **0.60** (was 0.75), unsure stays 0.25. And compare the target: the person sees several
results, so a search whose page 2 is the answer may be fine. `conf_top3.py` (output `conf_top3.txt`, OOF probabilities
`conf_top3_oof_<mode>.json`, refitted coefficients `conf_top3_coef.json`).

- **Label:** `top3_ok` = one of hits 1-3 matches any need, score.py's per-hit rule that counts `useful` (the script
  checks the per-hit count reproduces every stored `useful`, and that first right implies top-3 right).
- **Base rates:** keyword-only first right 59.7 %, top 3 right **78.5 %** (red 48.6 % / 73.9 %; 68 questions have the
  answer at 2 or 3 but not 1). Hybrid 76.2 % / **89.8 %** (red 71.6 % / 86.7 %; 49).
- **Fits:** same family (L2 logistic C = 0.3, grouped CV by topic, 5 x 20, out-of-fold). Feature set (a) = the
  committed signals; (b) = (a) + `cover_best3`, `cover_mean3`, `title_best3`, `all3` (one of 1-3 has every word group),
  `emerg3` (an emergency book in 1-3).

| mode | model | CV AUC own target | AUC on the other target | red, own | Brier (base rate) | calibration own target: 0-25 / 25-50 / 50-75 / 75-100 (n, predicted, actual) |
|---|---|---|---|---|---|---|
| keyword | **first-a** (committed) | **0.775** | 0.737 (top3) | 0.754 | 0.187 (0.241) | 25 .21 .20 / 107 .37 .36 / 113 .62 .65 / 117 .87 .85 |
| keyword | first-b | 0.768 | 0.721 | 0.752 | 0.189 | 30 .20 .23 / 109 .38 .32 / 106 .62 .70 / 117 .88 .85 |
| keyword | top3-a | 0.717 | 0.778 (first) | 0.680 | 0.156 (0.169) | 0 / 14 .44 .71 / 117 .64 .66 / 231 .88 .85 |
| keyword | top3-b | 0.778 | 0.732 | 0.776 | 0.144 | 1 .22 1.0 / 31 .43 .61 / 101 .63 .55 / 229 .90 .91 |
| hybrid | **first-a** (committed) | **0.737** | 0.756 (top3) | 0.697 | 0.159 (0.181) | 1 .23 1.0 / 26 .41 .46 / 139 .65 .62 / 196 .89 .90 |
| hybrid | first-b | 0.717 | 0.774 | 0.685 | 0.162 | 1 .24 1.0 / 24 .40 .46 / 139 .64 .65 / 198 .89 .88 |
| hybrid | top3-a | 0.718 | 0.738 (first) | 0.696 | 0.086 (0.092) | 0 / 3 .48 .67 / 27 .69 .74 / 332 .92 .91 |
| hybrid | top3-b | 0.765 | 0.719 | 0.769 | 0.081 | 0 / 5 .44 .60 / 35 .66 .69 / 322 .93 .93 |

The current signals describe the first page, so they predict "first right" better than "top 3 right" (the first-page
model even ranks top-3 rightness better than the same signals refitted for it: .737 vs .717, .756 vs .718). Only with
the top-3 signals does a top-3 model rank its own target as well (.778 / .765), and then it leans on `emerg3` with a
negative `emerg1`, which looks fitted to this emergency-heavy set.

**Policy at 0.60 / 0.25** (out-of-fold; FA = label true but below 0.60, slip = label false but at/above; red in brackets;
"none of 3 right but sure" is the real failure: no buttons and nothing useful in view):

| mode | model | sure / buttons / unsure | FA first | slips first | FA top3 | **none of 3 right but sure** | first right but "help me help you" |
|---|---|---|---|---|---|---|---|
| keyword | **first-a** | 180 (50 %) / 157 (43 %) / 25 (7 %) | 70 (41) | 34 (24) | 118 (81) | **14 (9)** | 5 (3) |
| keyword | first-b | 174 / 158 / 30 | 77 (42) | 35 (25) | 125 (82) | 15 (10) | 7 (4) |
| keyword | top3-a | 319 (88 %) / 43 / 0 | 12 (7) | 115 (86) | 28 (20) | 63 (44) | 0 |
| keyword | top3-b | 291 (80 %) / 70 / 1 | 23 (12) | 98 (72) | 42 (28) | 49 (33) | 0 |
| hybrid | **first-a** | 296 (82 %) / 65 (18 %) / 1 | 35 (27) | 55 (36) | 50 (38) | **21 (14)** | 1 (1) |
| hybrid | first-b | 296 / 65 / 1 | 38 (29) | 58 (39) | 50 (37) | 21 (14) | 1 (1) |
| hybrid | top3-a | 357 (99 %) / 5 / 0 | 2 (2) | 83 (59) | 2 (2) | 34 (26) | 0 |
| hybrid | top3-b | 349 (96 %) / 13 / 0 | 4 (4) | 77 (54) | 7 (6) | 31 (23) | 0 |

Every "unsure" question is also `urgent()` here except one (first-b keyword), so all of them still get their pages.

At the same share of buttons as first-a at 0.60 (50 % keyword, 18 % hybrid) the top-3-b model would need a cut of
0.84 / 0.83 and gives 10 vs 14 / 19 vs 21 "none of 3 right but sure", for 80 vs 70 / 34 vs 35 first-right questions
with buttons: a small gain, from a signal (`emerg3`) that may not hold off this set, and only with a different
threshold for each target.

**Decision: keep the first-page model, buttons at 0.60.** A top-3 model is calibrated for a target that is right
78-90 % of the time, so at 0.60 it almost never offers buttons and lets 2-4 times as many all-wrong searches through
(keyword 49-63 vs 14, hybrid 31-34 vs 21). The first-page model at 0.60 is the safer one for the failure that matters,
and still predicts top-3 rightness about as well as anything fitted for it. Chat simulation at 0.60 / 0.25
(`conf_policy.py`, `conf_policy_060.txt`): keyword-only answer 180 (50 %; 146 first right, 168 with a useful page),
buttons 157 (43 %), help me help you + pages 25 (7 %); hybrid 296 (82 %) / 65 (18 %) / 1. Conversations, keyword: 25
sure / 24 buttons / 3 below; hybrid 44 / 8 / 0. Unit tests: all 15 files pass (test_confidence 18, one new).

## Everyday questions: buttons only when very unsure, smaller (2026-11-18, later)

Owner: on everyday (not urgent) questions the buttons only when uncertainty is very high, and smaller; same choices.
Branch `fork/everyday-buttons` (worktree `.claude/worktrees/everyday-buttons`). `conf_everyday.py`: out-of-fold
first-page model on the 51 questions that are not urgent (no danger sign, not `urgent(q, corrected)`), both modes.

| cut | kw buttons | kw first right but buttons | kw top-3 right but buttons | kw none of 3 right, no buttons | hy buttons |
|---|---|---|---|---|---|
| 0.15 / 0.20 / 0.25 | 0 | 0 | 0 | 7 | 0 |
| 0.30 | 2 (4 %) | 0 | 1 | 6 | 0 |
| 0.35 / 0.40 | 5 (10 %) | 2 | 3 | 5 | 0 |
| 0.60 (before) | 16 (31 %) | 9 | 10 | 1 | 5 (10 %) |

Chosen: `EVERYDAY_BUTTONS = 0.30` (`LASTBOOK_CONF_BUTTONS_EVERYDAY`). The "help me help you" reply for everyday
questions: below min(UNSURE, everyday cut), so never without buttons. The `suggest` event gets `'style': 'compact'`;
choices unchanged (emergency set + Something else). Urgent questions unchanged.
