# Multi-turn search: follow-ups, corrections, noise, new emergencies (2026-11-18)

Base: upstream `main` 256d52f, full library. 52 invented conversations in `convos.py`, labelled by what the last message
is: follow-up (14), addition (19), correction (14), new emergency (5); 12 of them have a noise message in between
("jdjdk", "sorry wrong chat", "😭😭😭"). Scored on the last message's top 8 (`multiturn.py`, `score.py`).

## Strategies

- **latest**: upstream. Searches the latest message only.
- **fork**: the fork today (`assistant.chat`). The latest message's own search, plus the previous message joined
  with it, with the previous answer's citations first. Here those citations are approximated as the previous turn's
  top 3.
- **sensible**: as fork, but noise is skipped when choosing the previous message.
- **aware**: a no-model classifier.
  - Noise: no search, and buttons are shown.
  - Correction: the correction words are stripped, and pages already shown go last.
  - Anything else: this message's own best results first.
- **combined**: noise and corrections as in aware.
  - **A danger sign the session didn't have yet:** this message's own search first, and no pages carried over.
  - Otherwise, the fork's order, with "previous" meaning the last message that wasn't noise.
- **+typo**: the same, with typo correction first.

## First result right (hybrid / keyword-only)

| | follow | add | correct | new | after noise | all |
|---|---|---|---|---|---|---|
| latest | 43 / 29 | 32 / 37 | **64** / 57 | 60 / 60 | 33 / 33 | 46 / 42 |
| fork | **86** / 79 | **68** / 47 | 29 / 21 | **0 / 0** | **75** / 50 | 56 / 44 |
| aware | 43 / 29 | 32 / 37 | 50 / **64** | 60 / 60 | 25 / 33 | 42 / 44 |
| **combined** | **86 / 79** | 58 / **53** | 50 / **64** | **60 / 60** | 67 / **67** | **64 / 64** |

(sensible = fork on the first result; +typo changes nothing here except −2 to −8 points on keyword-only.)

- **The fork fails every new emergency:** "THE KITCHEN IS ON FIRE" after a water question gets water pages first. It
  also gets 29% of corrections, because it brings back the pages the person rejected.
- **Combined is never worse than both fork and latest,** and best overall on both setups.
- **Additions:** combined 58% against the fork's 68%. Two additions held a new danger sign and lost the carried pages.
- **Corrections:** 50% on hybrid, against latest's 64%.
- **The no-model classifier:**
  - Noise: 11 of 12. It misses autocorrect gibberish made of real words ("the duck is a mint").
  - Corrections: 14 of 14.
  - New emergencies: 0 of 5 on its own. They are caught only by the danger-sign words (15 entries, from
    `server.PHRASES`, `SYN` and a hand list), which flagged all 5.
- **The classifier was written alongside these cases,** so its accuracy here is optimistic.
- **19 of 52 combined first results are still wrong,** and most are retrieval problems rather than the strategy:
  - Off-topic books first: Machine-Shop Practice, Leather Manufacture, Calculus. The section split fixes the first
    two.
  - Danger words missing: "it was bleach" has no swallow/drank verb.

## Buttons

Combined shows buttons on every message it calls noise. Not measured yet: whether the person would tap them, and
whether showing them after a weak search (fewer than 3 results) is the right trigger.

## On the split library (whole-book pages cut into sections)

First result right, all 52 conversations, unsplit → split (`results_multiturn_split.json`):

| | hybrid | keyword-only |
|---|---|---|
| latest | 46 → 50 | 42 → 38 |
| fork | 56 → 58 | 44 → 46 |
| **combined** | **64 → 69** | 64 → 64 |

- **Hybrid, combined:** follow-ups 86 → 93, corrections 50 → 57, new emergencies 60 → 80.
- **Machine-Shop Practice in the top 8:** with hybrid it drops to 0 for every strategy except latest (6 → 2).
- **Useful pages** go up on every strategy and both setups.
- **Combined on hybrid,** 4 first results flipped from wrong to right: rabies, husband's burn, grease fire, gas smell.
  1 flipped the other way: "now he keeps vomiting", whose new first result is *Caring for Children*, arguably still
  a fair answer.
- **Keyword-only, after noise:** combined goes from 67 to 58. That's 1 of 12 conversations, so within noise.

## Not done

- **The E4B rewrite of the whole conversation into one search:** needs the model loaded.
- **Vector negative feedback,** moving the question away from rejected pages: not built.
- **The combined strategy on the split library:** not run.
