# Held-out check of the emergency detection (2026-11-19)

Code: `D:\git\lastbook`, branch `fork/lightweight-gemma-no-us-maps` at 4ea2d9f, unchanged. Data:
`LASTBOOK_DATA=D:\LastbookData-fork-test`, read-only (sections build refused, read-only index connections, vector file
never truncated, no model), as `../triage/body_eval.py`. `python -B -X utf8`. **Nothing was changed or tuned**: no code,
word list or threshold. The only judgement calls are in the scoring (which labelled signs count as "covered by
body_signs", the miss themes, the rough "health book" test), all in `indep_analyze.py`.

Set: `phrases.jsonl`, 690 lines written by an agent that never saw the code: 343 red, 104 yellow, 243 green (128 of
them counterexamples, 115 mild); 355 "web-inspired", 335 invented.

Files: `indep_eval.py` (one run per mode -> `runs/kw.json`, `runs/hy.json`), `indep_analyze.py` (-> `results.json`),
`indep_report.py` (the tables and appendices below). Keyword-only took 52 s, hybrid 478 s (semantic loaded).

**What is measured per line.** Text checks (identical in both modes, checked: 0 differences): `typos.correct` and what
it did to each word (split / fix / body_fix), `confidence.body_signs(text, corrected)`, `confidence.urgent`,
`assistant.is_danger`, `confidence.unknown_words(corrected)`. Then `assistant.turn_hits` as a first message: p, level,
route, and `assistant.chat_level` -> **answer** / **buttons** / **compact buttons** (everyday) / **ask** (the bare "help
me help you": no answer, pages only as consulted) / **ask+pages** (`UNSURE_DANGER`: pages, no answer); first 3 page
titles. "First page from an emergency book" is `confidence._emergency_book` on the first hit: **rough** — many good
health pages (e.g. "How to help a person having a seizure", "Heart Disease and High Blood Pressure") are not from a
book that test counts. A second, even rougher test (a health-looking word in the title) is used only to mark clearly
off-topic first pages.

## Headline

| | in-sample (BODY_SIGNS.md / CONFIDENCE.md / FORK 3l) | held-out, keyword-only | held-out, hybrid |
|---|---|---|---|
| **urgent()/is_danger, red** | **218/218 (100%)** | **293/343 (85%)** — 50 red lines not urgent | same (text check) |
| urgent, yellow | 49/72 (68%) | 79/104 (76%) | same |
| urgent, green (false positive) | 26/50 green, 18/22 counterexamples (61% together) | 155/243 (64%); counterexamples 103/128 (80%); mild 53/118 (45%) | same |
| danger signs (assistant.DANGER) alone, red | 81/218 (37%) | 78/343 (23%) | same |
| **body_signs, lines whose signs it claims to cover** | not measurable (list written on the set; 107 matches) | **158/236 (67%)**; right category 150/236 (64%); red 138/211 (65%) | same |
| body_signs, any line with a sign (most signs are outside its list) | – | 171/553 (31%); red 141/341 (41%) | same |
| body_signs false positives | "a few odd matches" | green 54/243 (22%); counterexamples 44/128 (34%); mild 10/118 (8%) | same |
| **red lines with the bare "help me help you"** | **0** (both modes) | **18 (5.2%)** | **4 (1.2%)** |
| red lines with pages withheld | 0 | 18 (the same 18) | 4 (the same 4) |
| red lines given pages but no answer (ask+pages) | 0 of the body-sign questions (cases: 24 of 362 overall) | 36 (10%) | 1 |
| red lines answered "sure" whose first page is not from an emergency book | not measured | 42 of 91 sure (23 with a non-health title) | 110 of 212 sure (59 with a non-health title) |
| red, first page from an emergency book (rough) | – | 94/343 (27%) | 119/343 (35%) |
| request to say more, all questions (ask + ask+pages) | 7% keyword-only, <1% hybrid | 102/690 (15%) | 8/690 (1.2%) |
| typo/glued/real-word-typo lines whose meaning word ends up right | 99 of 109 typo questions changed, 0 of 253 clean ones | 45/84 fixed, 2 partly; 15 wrong word, 19 left | same |
| clean (untagged) lines changed by the corrector | 0 of 253 | 165/606 (143 of those only an apostrophe, ~40 real words bent) | same |
| unknown_words fires | 0 of 426 | 4/690: "hlep", "HELP" (yellow), "hemmorage", "pleaseeee helpppp my babyy" (red) | same |

**How much the in-sample numbers overstated.** The headline in-sample claim, urgent on 218/218 red, is 85% on new
wording: **1 red line in 7 is not urgent**, and those are exactly the ones that can lose their pages. The safety
counts in BODY_SIGNS.md ("red questions with the bare ask after: 0", both modes) become 18 keyword-only and 4 hybrid;
ask+pages on red goes from 0 (body-sign questions) to 36 keyword-only. body_signs, which had no honest recall figure,
finds two thirds of the signs it is meant to cover. Every line that body_signs *does* catch is safe: 0 bare asks and
0 ask+pages among them, in both modes — the rule works, its word list is what's short. The false-positive side is
about as in-sample (urgent on 64% of green, 80% of counterexamples; the cost is only that pages are never held back).
Typo correction: in-sample "0 of 253 clean questions changed"; here 165 of 606 untagged lines change, mostly harmless
apostrophes, but about 40 real slang words are bent into other words ("keeled" -> peeled, "puking" -> poking,
"spewing" -> sewing, "blacked" -> blocked, "gasps" -> gaps, "seizes" -> sizes, "texted" -> tested, "dads" -> adds).
Web-inspired lines (closer to real messages) do no better than invented ones on urgency (176/202 red vs 117/141) and
are where the keyword-only ask+pages concentrate (29 of 36).

Hybrid is much safer on withholding (4 vs 18 bare asks, 1 vs 36 ask+pages) because its p is higher across the board
(mean 0.63 vs 0.43), not because it detects more: urgent and body are text checks, identical in both modes. The price is
the other critical failure: hybrid answers 212 red lines "sure", and 110 of them start on a page outside the emergency
books (59 on a title that isn't health at all: NEETS technician handbooks, a Honda Civic manual, a writing guide).

## The critical failures (full lists in Appendix A)

- **Bare "help me help you" on red** — keyword-only 18: "worst headache of my life came on like a thunderclap", "he
  took a whole box of paracetamol but he says he feels fine", the intussusception "red jelly poo" line, "old lady on the
  floor in the shop wont answer me", "let him sleep it off hes really drunk and cant stand", "she is not good, colour is
  like ash", "911" (no letters -> noise route, p 0.95, still asked), "hemmorage" (no pages at all), "he cant breed",
  "my son is having a sea sure", the rambling dad with a drooping mouth, the neighbour on the kitchen floor for 2 days,
  "im fine dont worry just cant feel the left side of my body", "she just took 20 of her sleeping tablets", "grandma ...
  hard to rouse", "he's out cold on the pavement", "she keeled over", "he dropped like a stone". **None is urgent()**;
  all have p < 0.25 except "911". Hybrid 4: "911", "hemmorage" (unknown_words cap), "sooo much bloooood" (p 0.225;
  "bloooood" is 3 edits from blood, so neither URGENT's blood\w* nor body_match sees it), "he dropped like a stone in the middle of
  football".
- **Pages withheld on red**: exactly the bare-ask lines above (18 / 4); no red line is withheld any other way.
- **Ask+pages on red** (pages but no answer): keyword-only 36 (all urgent but no body sign: fitting, shaking with eyes
  rolling, "throat closing up ate shrimp", button battery, mushroom, ice-cold and sleepy, labour/breech, head injury and
  sleepy, "i cut myself deep and it wont stop", "her heart is beating really slow like 30" ...); hybrid 1 ("pleaseeee
  helpppp my babyy").
- **"Sure" on red with a non-emergency first page**: keyword-only 42 of 91 (e.g. "no pulse" -> NASA Basics of Space
  Flight, "having a fit" -> Electronics factories, "lips blue" -> Role Playing); hybrid 110 of 212 ("no pulse" -> NEETS
  Module 12, "bleeing from head wont stop" -> NEETS Module 19, button battery -> Honda Civic manual, "she isnt braething"
  -> Newborns Babies and Breastfeeding). About half of these first pages are still health books the rough test doesn't
  count.

## body_signs by the category it covers (keyword run; text check)

| category | lines with it | any body sign found | the right one | urgent |
|---|---|---|---|---|
| breathing | 63 | 55 | 54 | 61 |
| unconscious | 59 | 34 | 24 | 47 |
| bleeding | 45 | 29 | 28 | 36 |
| choking | 20 | 16 | 14 | 19 |
| seizure | 20 | 11 | 9 | 18 |
| blue | 19 | 13 | 8 | 17 |
| chest pain | 17 | 11 | 8 | 17 |
| pulse / heartbeat | 13 | 6 | 6 | 13 |
| not moving | 8 | 8 | 8 | 8 |
| cold and clammy | 0 | – | – | – |

Breathing is well covered; unconscious, seizure, pulse and chest pain are the weak categories (their everyday wordings:
out cold, keeled over, fitting, shaking, eyes rolling, heart beating slow, elephant on my chest, tight chest).

## Typo / glued / real-word-typo correction (Appendix B lists all 84)

Compared loosely: the corrected text's content words against the "meaning" words (crude stem, exact), then read by hand
(7 overrides, in `HAND`).

| tag | n | fixed | partly | wrong word | left as typed | nothing to fix |
|---|---|---|---|---|---|---|
| typo | 55 | 34 | 2 | 9 | 8 | 2 |
| glued | 11 | 8 | 0 | 3 | 0 | 0 |
| real-word-typo | 20 | 3 | 1 | 4 | 11 | 1 |
| all (84 lines) | 84 | 45 | 2 | 15 | 19 | 3 |

- **Real-word typos are almost never fixed** (3/20): the corrector only touches words the library lacks, so
  "breeding", "braking", "breaking", "past out", "sea sure", "dropping" (drooping), "week" (weak), "attach", "cheat
  pain", "chest pane" stay; "bleating" -> beating, "brest" -> best, "breading" -> breeding, "seasure" -> measure are
  made into other real words. body_signs still catches some (it looks at the typed text with one-slip matching), but
  only 7/16 in-scope.
- **Wrong words from plain typos**: "strock" -> stock, "poisend" -> poised, "siezing" -> seizing (not matched by
  URGENT's seizure\w*), "bluding" -> blading, "nto" -> onto, "dady" -> day, "hesss" -> hess, "sooo" -> soo (bloooood
  left).
- **Left as typed**: "hemmorage", "unconshus", "anafilactic", "hart attack", "noo breath", "over dose", "blu lip", "hlep".
- **Glued**: 8/11 right; "myboyiscoking" -> my boy is cooking, "blueslipsandshaking" -> blue slips and shaking,
  "facedroopingslurring" -> face drooping slurry ing.

## Breakdown by kind tag and by source

Urgent and body columns are text checks (same in both modes); a tag can sit on any colour. "body: covered signs found"
counts lines whose labelled signs fall in body_signs' categories.

