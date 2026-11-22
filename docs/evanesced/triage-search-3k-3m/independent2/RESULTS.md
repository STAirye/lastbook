# Held-out list 2: before (4ea2d9f) vs after (19c2db2, fork/heldout-fixes)

Measurement only: no code, word list or threshold changed; nothing committed. 606 lines in `phrases.jsonl`
(249 red, 111 yellow, 246 green, 135 of them counterexamples, 109 mild), written blind. Six lines are also on list 1
("cantbreathe", "he got shot in the leg", "worst headache of my life came on like a thunderclap", "purple spots and stiff
neck and light hurts her eyes", "pregnant and heartburn every night", "seizure of assets by the bank"); leaving them
out changes no headline number (urgent red 85% → 92% without them, too).

How it was run (in-process, read-only, `LASTBOOK_DATA=D:\LastbookData-fork-test`, `sections.build` refused, index
opened read-only, vector file not truncated, no model, `python -B -X utf8`):

- `eval2.py`: a copy of `../heldout-fixes/heldout_eval.py` with only the input path changed to this folder. Before =
  `LASTBOOK_CODE=D:\git\lastbook` (4ea2d9f, clean apart from untracked `.claude/`), after =
  `LASTBOOK_CODE=D:\git\lastbook\.claude\worktrees\heldout-fixes` (19c2db2, clean). Keyword-only (`TH_KW=1`) and hybrid.
  Runs in `runs/{before,after}_{kw,hy}.json`.
- `analyze2.py`: imports `../heldout-fixes/compare.py` unchanged for the metrics (same definitions as list 1 /
  FORK.md 3l; "urgent" = `assistant.is_danger`), adds list 1's numbers beside them (list 1 before =
  `../independent/runs/{kw,hy}.json`, after = `../heldout-fixes/runs/ho_final_{kw,hy}.json`; they reproduce the FORK.md
  3l table exactly), writes `results.json` and `runs/report.txt` (every list in full).
- Text checks (urgent, body signs, correction) are identical in both modes, as before.

## The table

Keyword-only unless the row says otherwise. List 1's after-numbers are in-sample now (the fixes were built on it).

| | list 2 before | list 2 after | list 1 after (in-sample) |
|---|---|---|---|
| urgent: red | 211/249 (85%) | **230/249 (92%)** | 340/343 (99%) |
| urgent: yellow | 75/111 (68%) | **85/111 (77%)** | 98/104 (94%) |
| urgent: green (false positive) | 137/246 (56%) | **127/246 (52%)** | 76/243 (31%) |
| urgent: counterexamples | 92/135 (68%) | **82/135 (61%)** | 22/128 (17%) |
| urgent: mild | 43/109 (39%) | **43/109 (39%)** | 56/118 (47%) |
| body sign found, lines with a covered sign | 91/129 (71%) | **101/129 (78%)** | 200/236 (85%) |
| — red | 83/117 (71%) | **95/117 (81%)** | 177/211 (84%) |
| body sign on counterexamples | 42/135 (31%) | **39/135 (29%)** | 9/128 (7%) |
| red: bare ask, pages withheld (keyword / hybrid) | 17 / 2 | **0 / 0** | 0 / 0 |
| red: pages withheld, any reason (keyword / hybrid) | 18 / 2 | **1 / 0** | 0 / 0 |
| red: pages but no answer (ask+pages; keyword / hybrid) | 47 / 0 | **5 / 0** | 0 / 0 |
| all lines: pages withheld (keyword / hybrid) | 56 / 2 | **1 / 0** | 0 / 0 |
| plea replies | no bare plea on list 2 | — | "911", "HELP", "hlep" → plea |
| typo lines (42 typo/glued/real-word-typo) with the meaning word right | 13 fixed, 11 wrong word, 13 left, 3 partly, 2 nothing to fix | **18 fixed, 6 wrong, 13 left, 3 partly, 2 nothing** | 71/84 fixed, 6 wrong, 2 left |
| clean lines (564) with a real English word bent | 46 | **0** | 0 |
| red judged sure whose first page title isn't even health-looking (rough; keyword / hybrid) | 8 of 45 / 27 of 133 | **8 of 45 / 24 of 124** | 14 of 89 / 41 of 193 |

Other rows: red actions keyword-only went from answer 45 / ask 17 / ask+pages 47 / buttons 140 to answer 45 /
ask+pages 5 / buttons 199; hybrid from answer 133 / ask 2 / buttons 114 to answer 124 / buttons 125. All lines with
pages but no answer: 91 → 45 keyword-only, 0 → 0 hybrid. Red sure with the first page from an emergency book: 29 → 30
keyword-only, 60 → 62 hybrid. Nothing urgent before stopped being urgent on a red or yellow line.

## Overfitting gap

The before-numbers are about the same on both lists (urgent red 85% on both), so the gap after is the fixes not
carrying over to new wording:

- **Red recall:** list 1 went 85% → 99%, list 2 85% → 92%. Half the gain carried over (+7 points of +14). Red lines
  missed: 3 of 343 on list 1 (0.9%), 19 of 249 on list 2 (7.6%), about 8 times as many.
- **Yellow:** +18 points on list 1, +9 on list 2 (94% vs 77%). Half again.
- **False alarms:** this is the biggest gap. Counterexamples urgent went 80% → 17% on list 1 but only 68% → 61% on
  list 2: about a tenth of the gain carried over. Green overall: 31% vs 52%. Body signs on counterexamples: 7% vs 29%
  (−27 points on list 1, −2 on list 2). The idiom cuts (`NOT_URGENT`) catch the idioms they were written for, and
  almost none of the new ones.
- **Body signs:** +18 points on list 1, +7 on list 2 (85% vs 78%). Red only: 84% vs 81%, closer.
- **Typos:** list 1 85% fixed after; list 2 43% (18 of 42). "Left as typed" didn't move on list 2 (13 → 13) where it
  went 18 → 2 on list 1. Wrong words fell 11 → 6, as on list 1.
- **Fully carried over** (these were structural changes, not word lists): pages are never withheld (56 → 1 keyword,
  2 → 0 hybrid), urgent questions get an answer (red pages-but-no-answer 47 → 5, and the 5 left are the lines not
  urgent at all), and no clean line has an English word bent (46 → 0).

In short: the general mechanisms held up on new lines; the word lists (urgent wordings, idioms, body wordings, typo
fixes) are tuned to list 1 and give roughly half their red/yellow gain, and about a tenth of their false-alarm gain,
on wording they haven't seen.

## Critical lines after

### Red lines still not urgent (19), grouped by hand

- **Unresponsive or altered in other words (4):** "my mate is having a turn, can't get a word out of him", "my missus
  is having a do and she's grey", "something wrong with grandma she just staring and drooling", "found an old man
  outside in the snow, barely awake, skin icy"
- **Suicide or self-harm in other words (3):** "my son says voices are telling him to jump", "cant do this no more.
  took everything in the cabinet", "unalive myself tonight how many" (searched as "unlike myself")
- **Stroke, TIA, hypertensive (3):** "stoke symptoms my dad" (typo not fixed), "mum's speech went weird for 5 mins then
  back to normal", "my bp is very high 200 and my vision is going blurry"
- **Drug slang or antidote (2):** "my brother is ODing" (searched as "Oring"), "narcan how"
- **Airway (2):** "his throat is closing after peanuts", "child has croup and making squeaky noise even when calm"
- **One each:** bleeding without the word ("my mate chainsawed his thigh its pumping"), CPR by its parts
  ("compressions how fast"), GI bleed ("my poo is black and tarry and i feel a bit lightheaded"), chemical eye ("acid
  splashed in her eyes at work"), voice-to-text garble ("anna flack sis" = anaphylaxis)

8 of the 19 are answered "sure" with no buttons in keyword-only mode, from pages that aren't health pages ("my brother
is ODing" → *Making Therapy Functional and Fun*, "acid splashed in her eyes" → *Electronics factories*, "my son says
voices are telling him to jump" → *Story Telling*, "anna flack sis" → *Introductory Statistics*, "chainsawed his thigh"
→ *Range-of-motion exercises*, "narcan how" → an index page, "anafalactic shock" → *Microbiology*, "bleeding out" →
*NEETS Technicians Handbook*). The last two are urgent but still answered from off-topic first pages.

### Red lines with no answer or no pages after

- Keyword-only (6): pages but no answer (ask+pages, not urgent, so `UNSURE_PAGES`): "his throat is closing after
  peanuts", "cant do this no more. took everything in the cabinet", "unalive myself tonight how many", "my mate is
  having a turn, can't get a word out of him", "mum's speech went weird for 5 mins then back to normal". No pages:
  "he'snotbreathingwhatdoido" (urgent, body sign breathing, buttons, but the search finds nothing: the glued words
  aren't split because of the apostrophe).
- Hybrid: none.

### New false positives (green urgent after, not before): 9

"can i take ibuprofen with paracetamol for a headache" (mild; overdose medicine names), "server is not responding
since 3am" (body: unconscious), "the brakes are seizing up on my bike" (body: seizure), "he's out cold in the fantasy
league rankings" (body: unconscious), "zombie makeup grey skin tutorial", "how to tie a tourniquet for my first aid
exam", "the bus is packed i'm suffocating", "my battery is swollen and hot, vape", "the patient in my nursing case study
has sepsis, what are the bundle steps". Against these, 19 green lines stopped being urgent (mostly the idiom cuts:
"stroke of luck", "drowning in emails", "how to bleed a radiator", "seizure of assets by the bank"...): net −10.

### Typo damage after

- English words bent (the table's metric): 1 line, "he is chocking on fold" (chocking → choking, which is right).
- Read by hand, words still turned into another word (all already wrong in 4ea2d9f; 19c2db2 adds none): rennie →
  ronnie, ODing → Oring, gouching → touching, gurgly → gargle, unalive → unlike, konked → kinked, tbh → tbu, redback →
  repack, dhe → due, stooling → stooping, ako → amo, fluey → flue, doms → dams, sniffly → stiffly (2), sipon → sion,
  fortnite → fortunate (2), elden → eden, bjj → bmj, adobo → adobe. These are slang, brand, drug, Filipino and game words
  that aren't in the English list, so the "English word bent" metric doesn't see them.
- **"hasnt", "havent", "shouldnt" → "hasn", "haven", "shouldn" (7 lines, before and after):** the t is dropped and the
  negation with it ("baby hasn moved all day", "haven slept in 4 days", "hasn peed all day"). The meaning flips for
  the search words.
- Fixed by 19c2db2: all 46 clean-line bends (keeled, fella, spewing, missus, crook, poo, calpol, giddy, invincible...),
  "seasure" → seizure (was "measure"), "anafalactic" → anaphylactic (was split into "an a faa ctic"), "shes not
  breaking" → breathing, "my dad has chess pain" → chest, "her face is dropping" → drooping, "helpppp", "wont wake
  uppp".

## By kind tag (keyword-only; hybrid is the same for urgent and body, and 0 red withheld after in every tag)

| tag | n (r/y/g) | urgent red before → after | yellow | green (FP) | body, covered signs | red withheld (kw) |
|---|---|---|---|---|---|---|
| plain | 100 (57/42/1) | 50 → 54 | 32 → 36 | 1 → 1 | 19 → 22 /24 | 4 → 0 |
| counterexample | 135 (0/0/135) | – | – | 92 → 82 | – | – |
| mild | 109 (0/0/109) | – | – | 43 → 43 | 1 → 0 /3 | – |
| fragment | 71 (45/15/11) | 37 → 39 | 7 → 7 | 3 → 3 | 18 → 19 /23 | 0 → 0 |
| child | 67 (37/19/11) | 36 → 36 | 14 → 16 | 5 → 5 | 8 → 9 /11 | 0 → 0 |
| slang | 64 (28/10/26) | 17 → 22 | 6 → 8 | 16 → 15 | 8 → 12 /18 | 7 → 0 |
| elderly | 39 (24/9/6) | 17 → 21 | 6 → 8 | 1 → 1 | 8 → 8 /11 | 2 → 0 |
| baby | 34 (19/5/10) | 19 → 19 | 5 → 5 | 9 → 9 | 7 → 6 /9 | 0 → 0 |
| misconception | 33 (20/5/8) | 18 → 20 | 4 → 5 | 4 → 4 | 6 → 7 /12 | 1 → 0 |
| non-native | 32 (17/7/8) | 15 → 16 | 4 → 4 | 3 → 2 | 8 → 9 /14 | 0 → 0 |
| typo | 25 (22/2/1) | 18 → 21 | 1 → 1 | 0 → 0 | 14 → 14 /16 | 0 → 0 |
| pregnancy | 22 (9/8/5) | 9 → 9 | 5 → 5 | 3 → 3 | 2 → 2 /4 | 0 → 0 |
| **mental-health** (new) | 14 (6/6/2) | **2 → 3** | 3 → 3 | 0 → 0 | 1 → 1 /1 | 3 → 0 |
| **buried** (new) | 13 (13/0/0) | 12 → 13 | – | – | 3 → 5 /6 | 1 → 0 |
| glued | 9 (8/0/1) | 8 → 8 | – | 1 → 1 | 5 → 5 /5 | 1 → 1 |
| **voice-to-text** (new) | 9 (9/0/0) | 8 → 8 | – | – | 4 → 5 /5 | 0 → 0 |
| real-word-typo | 8 (8/0/0) | 8 → 8 | – | – | 4 → 5 /7 | 0 → 0 |
| caps | 7 (5/1/1) | 5 → 5 | 1 → 1 | 1 → 1 | 3 → 3 /3 | 0 → 0 |
| rambling | 6 (5/0/1) | 4 → 5 | – | 1 → 1 | 2 → 3 /3 | 1 → 0 |

The weakest tag is **mental-health: 3 of 6 red lines urgent** after (list 1's suicide wordings didn't generalise:
"voices telling him to jump", "took everything in the cabinet", "unalive myself"). Slang gained most (17 → 22 of 28) but
is still the lowest-recall large tag (79%). Buried emergencies are all caught (13/13); voice-to-text 8/9 (only "anna
flack sis" missed).

## Remaining misses by theme

All red/yellow lines with any miss after (not urgent, a covered body sign missed, or red pages withheld in either
mode): 67. Grouped (regex first, by hand for the red ones above; full lists in `runs/report.txt` and `results.json`):

| theme | lines | examples |
|---|---|---|
| breathing, airway and colour without the urgent words | 12 | "he was eating steak n now he's making no sound just pointing at his neck", "is it normal for someone to go grey and stop answering", "baby born not crying not pink", "baby is chalking on milk", "helpppp hes blue" (urgent, body sign missed) |
| unresponsive in other words | 9 | "my friend took ket and is lying on the floor not answering", "my father fell down and not getting up, eyes are white", "she konked out and isnt waking" (urgent but body missed), "having a turn" |
| yellow conditions with no urgent word | 10 | "pinky finger bent sideways", "hiv exposure condom broke last night", "toes black and blistered after the mountain", "glass in his foot" |
| stroke, vision, blood pressure | 5+2 | "sudden curtain coming down over my vision in one eye", "pressure is 185/110 bit of a headache", "speech went weird for 5 mins" |
| mental health | 5 | the 3 red above, and yellow "my mum hasnt eaten in a week since dad died", "i feel so low i dont see the point" |
| bleeding (pumping, clots in pregnancy, spotting) | 3 | "chainsawed his thigh its pumping", "im 16 weeks and i'm passing big clots" |
| chest (clutching, compressions) | 4 | "she is 50 and clutching her chest", "my heart attack my chest" (urgent, body missed) |
| vomiting and diarrhoea in non-native or slang words | 4 | "loose motions", "LBM", "chundered 8 times" |
| seizures in other words | 2 | "having convulsion and her body is very hot", "my wife has a sizzler and wont stop shaking" |
| drugs, pregnancy, child, heat/cold, other | 11 | "my brother is ODing", "narcan how", "waters might have gone", "spilled hot tea on my toddler", "mi hijo no respira bien" |

False alarms that remain (127 green urgent after) are mostly the bare body word in another sense: "choking"
(wifi, printer, calculus), "bleeding" (stocks, engine, goals, tyre), "heart attack" (laptop, the bill), "dead"
(hard drive, tired), "baby" (9 everyday baby questions), "fever" / "rash" on mild lines, "battery" and "ate" (crayon,
sand, sock), and game words (Pokémon poison, Elden Ring bleed, Minecraft drowning, Sims baby not breathing).
