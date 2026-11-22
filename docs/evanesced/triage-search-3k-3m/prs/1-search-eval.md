Library search: test sets, scorer and a recorded baseline (triage search, part 1 of 8)

## What changes

No app code changes. This adds a measuring tool and a methods document:

- `tools/search_eval/`: test sets for the library search, a scorer, and a baseline recorded on `main`.
  - `data/`: the triage set (362 questions over 159 topics: 253 clean, red / yellow / green, 22 counterexamples
    such as "how to bleed the brakes", 109 typo versions), #128's 52, #154's 32 (+ 32 typos), #241's 21,
    48 glued or garbled messages, 52 conversations. Each case lists the words a useful page must contain and,
    for counterexamples, what must not come first. One shared pattern table (157 regexes).
  - `lists/`: four independent lists (690, 606, 531 and 832 messages), labelled red / yellow / green. Lists 1-3
    were written by AI agents of one model family told not to open any project file; list 4 by Qwen3.5-9B, run
    locally (mostly Spanish idioms). Each file's first line says who wrote it, its counts, and for which fixes it
    is no longer blind.
  - `score.py`: runs each question through `assistant.hybrid` (what `/api/retrieve` and the chat's first search
    return) or `server.find` (the Library tab), in-process, keyword-only or hybrid, and counts useful pages of 8,
    first useful, any of top 3, covered, topic cap broken; for the lists, pages shown and, once an urgency check
    exists, red / yellow / green flagged urgent (`n/a` on `main`). It only reads the library folder given by
    `LASTBOOK_DATA`.
  - `README.md`: what each set is, how to run it, what each measure means.
  - `baseline-main.json`: the summary counts on `main`.
- `docs/TRIAGE-SEARCH.md`: the methods for the whole triage-based search engine: every formula, constant and
  measure, how each number was measured, and the sources. The modules it describes arrive in PRs 2-8.

## Why

Issue #154 asked for search that treats a question as triage: an urgent question must get a useful first page,
and an everyday question that uses an emergency word ("bleed the brakes") must not get first aid. Proposal: #{ISSUE}.
Before changing the search, this gives a shared, rerunnable measure of the library's pages, so every later PR can
show its numbers against the same baseline. It complements #241, which tests the guide search (`web/words.js`),
and #302's emergency fallback for drowning, hypothermia and carbon monoxide searches.

## How it was tested

Run on `main` (5e656fb) against a copy of the Medium library pack (built 2026-11-12, with its meaning index of
337,016 passages), read-only. File sizes and times in the data folder were the same before and after.

| Set | Mode | n | useful of 8 (mean) | first useful | any of top 3 | covered | no useful page | topic cap broken |
|---|---|---|---|---|---|---|---|---|
| Triage, red | keyword | 131 | 3.89 | 58 | 96 | 89 | 27 | 4 |
| Triage, red | hybrid | 131 | 5.11 | 88 | 111 | 114 | 5 | 3 |
| Triage, yellow | keyword | 56 | 5.05 | 39 | 46 | 49 | 6 | 0 |
| Triage, yellow | hybrid | 56 | 5.86 | 42 | 51 | 54 | 1 | 0 |
| Triage, green | keyword | 44 | 5.77 | 36 | 41 | 40 | 1 | 0 |
| Triage, green | hybrid | 44 | 6.84 | 37 | 42 | 43 | 0 | 0 |
| Triage, counterexamples | keyword | 22 | 4.91 | 14 | 18 | 19 | 2 | 0 |
| Triage, counterexamples | hybrid | 22 | 5.73 | 17 | 20 | 22 | 0 | 0 |
| Triage, typo versions | keyword | 109 | 2.23 | 30 | 47 | 42 | 54 | 3 |
| Triage, typo versions | hybrid | 109 | 3.39 | 49 | 74 | 71 | 23 | 2 |
| #128, clean | keyword | 27 | 4.44 | 16 | 23 | 23 | 3 | 0 |
| #128, clean | hybrid | 27 | 5.93 | 24 | 26 | 27 | 0 | 0 |
| #128, typos | keyword | 25 | 3.6 | 13 | 16 | 16 | 7 | 0 |
| #128, typos | hybrid | 25 | 4.72 | 15 | 19 | 20 | 4 | 0 |
| #154, clean | keyword | 32 | 4.47 | 20 | 27 | 27 | 3 | 2 |
| #154, clean | hybrid | 32 | 5.47 | 20 | 29 | 27 | 3 | 1 |
| #154, typos | keyword | 32 | 2.91 | 13 | 19 | 15 | 12 | 2 |
| #154, typos | hybrid | 32 | 4.16 | 14 | 25 | 25 | 2 | 1 |
| #241 | keyword | 21 | 4.81 | 12 | 20 | 19 | 0 | 1 |
| #241 | hybrid | 21 | 5.71 | 14 | 21 | 20 | 0 | 0 |
| Conversations (last message) | keyword | 52 | 3.23 | 22 | 27 | 30 | 18 | 1 |
| Conversations (last message) | hybrid | 52 | 3.98 | 24 | 34 | 39 | 10 | 1 |
|   corrections | keyword | 14 | 4.43 | 8 | 10 | 10 | 3 | 1 |
|   corrections | hybrid | 14 | 5.07 | 9 | 10 | 13 | 1 | 1 |
|   new emergency | keyword | 5 | 4.4 | 3 | 4 | 4 | 0 | 0 |
|   new emergency | hybrid | 5 | 5.4 | 3 | 5 | 5 | 0 | 0 |

#154's own useful count (keyword): 141 of 256 clean, 101 of 256 typos. 
#154's own useful count (hybrid): 177 of 256 clean, 143 of 256 typos. 

| List | Mode | red: pages shown | red: no pages | yellow: pages shown | green: pages shown | flagged urgent |
|---|---|---|---|---|---|---|
| 1 | keyword | 318/343 | 25 | 102/104 | 242/243 | n/a |
| 1 | hybrid | 343/343 | 0 | 104/104 | 243/243 | n/a |
| 2 | keyword | 238/249 | 11 | 111/111 | 245/246 | n/a |
| 2 | hybrid | 249/249 | 0 | 111/111 | 246/246 | n/a |
| 3 | keyword | 194/199 | 5 | 78/78 | 254/254 | n/a |
| 3 | hybrid | 199/199 | 0 | 78/78 | 254/254 | n/a |
| 4 | keyword | 115/115 | 0 | 153/153 | 564/564 | n/a |
| 4 | hybrid | 115/115 | 0 | 153/153 | 564/564 | n/a |

Glued emergencies (keyword): first useful 0 of 18, no result at all 18. 
Glued emergencies (hybrid): first useful 1 of 18, no result at all 0.

The search code (`server.py`, `assistant.py`, `retrieval.py`, `engine/`) is unchanged on `main` up to 9645686, so
the baseline holds there too. Keyword-only took about 4 minutes, hybrid about 27.

What the numbers say on `main`: typo versions get 2.23 useful pages of 8 keyword-only (3.39 hybrid), against 3.89
(5.11) for the clean red questions; 27 of 131 clean red questions have no useful page keyword-only. Glued emergencies
("hesnotbreathing") find nothing keyword-only. 25 red lines of list 1 get no pages at all keyword-only. These are
the gaps the next PRs address. The typo figures 2.23 and 3.39 equal what was measured on the author's fork before
the changes, a check that the scorer reproduces the earlier runs.

Commands:

```
set LASTBOOK_DATA=<library folder>
python -B tools/search_eval/score.py --mode keyword --out kw.json
python -B tools/search_eval/score.py --mode hybrid --out hy.json
```

No unit tests change: the tool is not part of the test suite (like the other `tools/` scripts).

## What it doesn't do

- It changes nothing in the app.
- The lists have no "useful page" patterns: for them it counts pages shown and, later, urgency, not which page
  comes first.
- The confidence model's fitting script and the encyclopedia comparison are not included; they belong with
  PR 5 and PR 4.
- Text is English except list 4's Spanish lines.

Part 1 of 8 of the triage-based search engine (proposal: #{ISSUE}); builds on `main` (the first in the series).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
