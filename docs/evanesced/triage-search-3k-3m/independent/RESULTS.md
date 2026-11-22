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

| group | n (r/y/g) | urgent: red | yellow | green (FP) | body: covered signs found | red bare ask kw / hy | red ask+pages kw / hy | red first page from emergency book kw / hy |
|---|---|---|---|---|---|---|---|---|
| plain | 144 (100/43/1) | 89/100 | 31/43 | 0/1 | 49/64 | 4 / 0 | 17 / 0 | 30/100 / 38/100 |
| typo | 55 (45/8/2) | 35/45 | 5/8 | 0/2 | 22/31 | 1 / 2 | 1 / 1 | 17/45 / 23/45 |
| glued | 11 (11/0/0) | 10/11 | – | – | 8/10 | 0 / 0 | 0 / 0 | 5/11 / 6/11 |
| real-word-typo | 20 (20/0/0) | 16/20 | – | – | 7/16 | 2 / 0 | 0 / 0 | 4/20 / 4/20 |
| slang | 69 (31/10/28) | 25/31 | 7/10 | 21/28 | 18/26 | 3 / 1 | 5 / 0 | 4/31 / 7/31 |
| non-native | 25 (21/1/3) | 18/21 | 1/1 | 3/3 | 8/16 | 1 / 0 | 2 / 0 | 4/21 / 6/21 |
| fragment | 93 (57/13/23) | 44/57 | 8/13 | 11/23 | 21/34 | 3 / 3 | 2 / 1 | 22/57 / 22/57 |
| misconception | 40 (24/6/10) | 21/24 | 6/6 | 7/10 | 8/14 | 1 / 0 | 1 / 0 | 7/24 / 11/24 |
| child | 60 (31/12/17) | 25/31 | 10/12 | 9/17 | 12/18 | 2 / 0 | 4 / 0 | 7/31 / 7/31 |
| baby | 38 (26/4/8) | 26/26 | 4/4 | 6/8 | 12/17 | 0 / 0 | 1 / 1 | 5/26 / 7/26 |
| elderly | 32 (17/13/2) | 13/17 | 10/13 | 0/2 | 3/13 | 3 / 0 | 5 / 0 | 4/17 / 2/17 |
| pregnancy | 24 (14/7/3) | 13/14 | 6/7 | 2/3 | 5/5 | 0 / 0 | 3 / 0 | 1/14 / 2/14 |
| caps | 11 (8/3/0) | 7/8 | 3/3 | – | 6/8 | 0 / 0 | 1 / 0 | 3/8 / 4/8 |
| rambling | 11 (9/0/2) | 5/9 | – | 1/2 | 2/6 | 3 / 0 | 2 / 0 | 3/9 / 2/9 |
| counterexample | 128 (0/0/128) | – | – | 103/128 | – | 0 / 0 | 0 / 0 | – / – |
| mild | 118 (0/3/115) | – | 1/3 | 52/115 | 8/10 | 0 / 0 | 0 / 0 | – / – |
| source: web-inspired | 355 (202/95/58) | 176/202 | 73/95 | 25/58 | 80/115 | 10 / 2 | 29 / 0 | 54/202 / 75/202 |
| source: invented | 335 (141/9/185) | 117/141 | 6/9 | 130/185 | 78/121 | 8 / 2 | 7 / 1 | 40/141 / 44/141 |

## Miss themes (what a later fix would target; nothing fixed here)

126 red/yellow lines have at least one miss (not urgent, a covered body sign not found, or red pages withheld in
either mode). Themes are assigned by regex on the text and labelled signs (then the meaning), first match wins, so
counts are approximate; every line is in Appendix C.

| # | theme | lines | what misses | examples |
|---|---|---|---|---|
| 1 | Unconscious euphemisms | 17 | urgent and body | "he turned a funny colour and slumped", "old lady on the floor ... wont answer me", "he's out cold on the pavement", "hard to rouse", "found him face down in the pond", "grandpa ... snoring loud cant wake him" (cant wake ≠ won't wake) |
| 2 | Real-word autocorrect / real-word typos | 13 | urgent, body, correction | "she is breeding a lot from the leg", "he cant breed", "hes not braking", "she is not breaking", "my son is having a sea sure", "he past out", "she keeled over" (-> peeled), "strock", "poisend", "brest/cheat pain", "chest pane" |
| 3 | Misspellings the corrector leaves or bends | 10 | urgent, body | "hemmorage", "unconshus man", "siezing" (-> seizing), "tournaquet", "blu lip baby", "sooo much bloooood", "pnemonia", "cellulitus" |
| 4 | Bleeding without blood/bleed | 10 | body (urgent mostly ok) | "i cut myself deep and it wont stop", "finger cut off", "he got shot in the leg", "bitten on the neck and its pouring", "cut on his shin that wont stop oozing ... warfarin", "heavy period soaking pad every hour", "nosebleed wont stop", "vomit looks like coffee grounds" |
| 5 | Yellow conditions with no urgent word | 10 | urgent | "my 2 yr old put a bead up her nose", "mum dementia hasnt peed all day", "erection lasting 5 hours", "ankle crunched ... cant stand on it", "broke my nose", "cat scratch ... swollen and red" |
| 6 | Chest pain / heart wordings | 9 | body | "feels like an elephant sitting on my chest", "tight chest jaw ache feel sick 58 m", "heart racing like crazy", "her heart is beating really slow like 30", "i cant feel his heart beating", "my mother she have pain in heart" |
| 7 | Stroke words | 9 | urgent | "mum suddenly cant lift her right arm and talking funny", "his smile is crooked", "cant feel the left side of my body", "cant really say words right ... dribbling out the side of his mouth", "sudden blind in one eye like a curtain", "had a funny turn", "come over all peculiar". (URGENT has droop/slurr/stroke/face, so the textbook words work; the lay words don't) |
| 8 | Overdose / poisoning without the word | 8 | urgent | "took a whole box of paracetamol but he says he feels fine", "took 20 of her sleeping tablets to rest", "let him sleep it off hes really drunk", "the child is drinking the cleaning water", "over dose on xanax", "took 2 extra panadol" (pills? is in URGENT; tablets isn't) |
| 9 | Seizure slang | 7 | body | "shes fitting and wont stop been 6 minutes" (the fit phrase wants "having/had a fit"), "shaking all over on the floor and foam from mouth", "HES SHAKING AND HIS EYES ARE ROLLING", "swallow his tongue" |
| 10 | Bare word / greeting / number | 5 | urgent, noise | "911" (noise route, asked), "hlep", "helo my son", head injury with repeated questions |
| 11 | CPR named, no body word | 3 | body only (urgent ok) | "how do i do cpr on a man", "how many pushes for cpr baby" |
| 12 | Suicide euphemisms | 3 | urgent | "killing myself tonight" (URGENT has kill (him\|her\|my...)sel\w*, not "killing myself"), "my friend texted goodbye and wont answer", "i want to disappear forever" |
| 13 | Agonal / noisy breathing | 2 (+2 under #1) | urgent, body | "she's gurgling", "stridor croup barky cough 3am", snoring lines |
| 14 | Non-English | 2 | urgent, body | "mi esposa no respira help" (urgent only via help), "ma tête tourne et je vois flou soudain" |
| – | Others, 1–2 each | 18 | urgent | blue alone ("hes blue"), can't feel legs / tight cast, cold exposure ("brandy hes frozen"), pregnancy ("leaking fluid 30 weeks"), misconceptions ("suck the venom out", "finger sweep"), eye ("hit by a firework cant see"), "worst headache ... thunderclap", "under the bath water", "red jelly poo", "asthma attack inhaler not working", "throat closing up ate shrimp", "colour is like ash" |

Cross-cutting: **allergy words** ("throat closing up", "tongue feels huge and itchy", "used the epi pen") are urgent
through other words ("ate", "medicine", "hospital") and so only reach ask+pages keyword-only; none is a body sign.
**Elderly** lines are the weakest tag (body 3/13 covered, 3 bare asks keyword-only), **rambling** next (urgent 5/9
red, 3 bare asks): the long-message p is low and the signs are in lay words.

**False positives** (for completeness; they cost only that pages are shown and the buttons are full-size): urgent on
green is driven by burn (9), bleeding (9), blood (7), cut (6), baby (6), head, bleed, heart, dead, blue, stroke (5
each). body_signs fires on 54 green lines, 44 of them counterexamples ("how to bleed brakes on bike", "breathing exercises
for yoga", "blood orange cake", "choking hazard toys age 3", "pulse lentils recipe"...; Appendix D).

## Appendix A: critical failures, in full

### keyword-only: red lines that get the bare "help me help you" (ask, no answer, pages only as consulted) — 18

- "worst headache of my life came on like a thunderclap" — p 0.231, ask, urgent NO
- "he took a whole box of paracetamol but he says he feels fine" — p 0.237, ask, urgent NO
- "my son wont stop crying and his tummy is hard and he pulls his legs up and theres red jelly poo" (searched "my son won't stop crying and his tummy is hard and he pulls his legs up and theres red jelly poor") — p 0.213, ask, urgent NO
- "old lady on the floor in the shop wont answer me" (searched "old lady on the floor in the shop won't answer me") — p 0.174, ask, urgent NO
- "let him sleep it off hes really drunk and cant stand" (searched "let him sleep it off he's really drunk and can't stand") — p 0.156, ask, urgent NO
- "she is not good, colour is like ash" — p 0.152, ask, urgent NO
- "911" — p 0.947, ask, urgent NO, route noise
- "hemmorage" — p 0.2, ask, urgent NO, no pages found
- "he cant breed" (searched "he can't breed") — p 0.224, ask, urgent NO
- "my son is having a sea sure" — p 0.176, ask, urgent NO
- "ok so sorry if this is dumb but my dad keeps saying hes fine but he cant really say words right since lunch and his coffee keeps dribbling out the side of his mouth should i wait for my mum to get home" (searched "ok so sorry if this is dumb but my dad keeps saying he's fine but he can't really say words right since lunch and his coffee keeps dribbling out the side of his mouth should i wait for my mum to get home") — p 0.15, ask, urgent NO
- "my neighbour is old and lives alone, i havent seen her for 2 days, i looked through the window and shes on the kitchen floor and moving her hand a bit" (searched "my neighbour is old and lives alone, i haven seen her for 2 days, i looked through the window and she's on the kitchen floor and moving her hand a bit") — p 0.163, ask, urgent NO
- "im fine dont worry just cant feel the left side of my body" (searched "im fine don't worry just can't feel the left side of my body") — p 0.131, ask, urgent NO
- "she is ok i think she just took 20 of her sleeping tablets to rest" — p 0.2, ask, urgent NO
- "grandma keeps falling asleep in the chair more than usual and is hard to rouse" — p 0.203, ask, urgent NO
- "he's out cold on the pavement after the fight" — p 0.245, ask, urgent NO
- "she keeled over" (searched "she peeled over") — p 0.238, ask, urgent NO
- "he dropped like a stone in the middle of football" — p 0.217, ask, urgent NO

### keyword-only: red lines whose pages are withheld — 18 (the same lines: every withheld red line is a bare ask)

### keyword-only: red lines given pages without an answer (ask+pages, UNSURE_DANGER) — 36

- "grandpa fell over in the garden snoring loud cant wake him" (searched "grandpa fell over in the garden snoring loud can't wake him") — p 0.158, ask+pages, urgent yes
- "my kid ate one of those little round batteries from the remote" — p 0.212, ask+pages, urgent yes
- "shes fitting and wont stop been 6 minutes" (searched "she's fitting and won't stop been 6 minutes") — p 0.156, ask+pages, urgent yes
- "he is shaking all over on the floor and foam from mouth" — p 0.236, ask+pages, urgent yes
- "dads face is drooping and his words are coming out all wrong" (searched "adds face is drooping and his words are coming out all wrong") — p 0.19, ask+pages, urgent yes
- "throat closing up ate shrimp" — p 0.249, ask+pages, urgent yes
- "used the epi pen shes better now do we still need to go hospital" (searched "used the epi pen she's better now do we still need to go hospital") — p 0.15, ask+pages, urgent yes
- "tongue feels huge and itchy after new medicine" — p 0.225, ask+pages, urgent yes
- "he was drowning but now hes fine just coughing alot" (searched "he was drowning but now he's fine just coughing lot") — p 0.166, ask+pages, urgent yes
- "whole family has headache and dizzy and the dog is sleepy heater on" — p 0.249, ask+pages, urgent yes
- "ate a mushroom from the garden and now vomiting" — p 0.213, ask+pages, urgent yes
- "she stopped shivering but shes still ice cold and sleepy" (searched "she stopped shivering but she's still ice cold and sleepy") — p 0.224, ask+pages, urgent yes
- "fell off ladder hit head now being sick" — p 0.216, ask+pages, urgent yes
- "banged his head and now hes really sleepy and confused" (searched "banged his head and now he's really sleepy and confused") — p 0.205, ask+pages, urgent yes
- "baby coming now cant get to hospital" (searched "baby coming now can't get to hospital") — p 0.199, ask+pages, urgent yes
- "rash that doesnt go away when i press a glass on it and hes got fever" (searched "rash that doesn't go away when i press a glass on it and he's got fever") — p 0.238, ask+pages, urgent yes
- "she is wheezing and her ribs are sucking in and she can only say one word" — p 0.24, ask+pages, urgent yes
- "i cut myself deep and it wont stop" (searched "i cut myself deep and it won't stop") — p 0.152, ask+pages, urgent yes
- "her heart is beating really slow like 30" — p 0.174, ask+pages, urgent yes
- "my wife is in labour and the baby is coming but its bum first" — p 0.202, ask+pages, urgent yes
- "HELP ME HES SHAKING AND HIS EYES ARE ROLLING" (searched "HELP ME HE'S SHAKING AND HIS EYES ARE ROLLING") — p 0.175, ask+pages, urgent yes
- "pleaseeee helpppp my babyy" (searched "pleaseeee helpppp my baby") — p 0.2, ask+pages, urgent yes
- "give her salt water to make her sick she ate pills" — p 0.196, ask+pages, urgent yes
- "i dont know if this is anything but my 80 yo mum has been a bit off today not eating, mixing up words, tonight she seems really drowsy and her wee smells strong" (searched "i don't know if this is anything but my 80 yo mum has been a bit off today not eating, mixing up words, tonight she seems really drowsy and her were smells strong") — p 0.186, ask+pages, urgent yes
- "we were hiking and my wife slipped on the rocks and hit her head she was out for maybe a minute and now shes awake but keeps asking the same questions over and over" (searched "we were hiking and my wife slipped on the rocks and hit her head she was out for maybe a minute and now she's awake but keeps asking the same questions over and over") — p 0.151, ask+pages, urgent yes
- "lol my grandpa just fell and now cant talk properly" (searched "lol my grandpa just fell and now can't talk properly") — p 0.187, ask+pages, urgent yes
- "toddler drank a bit of hand sanitiser" — p 0.242, ask+pages, urgent yes
- "my child ate a whole bottle of gummy vitamins with iron" — p 0.229, ask+pages, urgent yes
- "paint thinner splashed in my eyes burning" — p 0.217, ask+pages, urgent yes
- "rash all over after starting new tablets and blisters in mouth" — p 0.223, ask+pages, urgent yes
- "my wife pregnant 8 month, much water coming" — p 0.229, ask+pages, urgent yes
- "the old man fall in the bath, he is cold and talk little" — p 0.192, ask+pages, urgent yes
- "my nan swallowed her denture plate i think shes coughing" (searched "my nan swallowed her denture plate i think she's coughing") — p 0.227, ask+pages, urgent yes
- "my arm is suddenly dead and my face feels weird" — p 0.161, ask+pages, urgent yes
- "she's got the shakes and is burning up after chemo" — p 0.132, ask+pages, urgent yes
- "fell through ice on the lake got him out" — p 0.201, ask+pages, urgent yes

### keyword-only: red lines judged "sure" (answered, no buttons) whose first page is not from an emergency/first-aid book — 42 of 91 sure red lines; 23 of them with a title that doesn't even look like health (marked **off**)

- "help blood" — p 0.994, answer, urgent yes, body bleeding — first: How to Recognize Life-Threatening Bleeding p.None
- "lips blue" — p 0.78, answer, urgent yes, body blue — first: Role Playing p.12 **off**
- "he turned a funny colour and slumped" — p 0.303, answer, urgent NO — first: Communicating with children p.13
- "no pulse" — p 0.811, answer, urgent yes, body pulse — first: NASA Basics of Space Flight - Chapter 13: Navigation p.3 **off**
- "no hartbeat what do" (searched "no heartbeat what do") — p 0.867, answer, urgent yes, body pulse — first: Heart Disease and High Blood Pressure p.17
- "having a fit" — p 0.698, answer, urgent yes, body seizure — first: Electronics factories p.24 **off**
- "chest pain" — p 0.78, answer, urgent yes, body chest pain — first: Heart Disease and High Blood Pressure p.18
- "mum suddenly cant lift her right arm and talking funny" (searched "mum suddenly can't lift her right arm and talking funny") — p 0.311, answer, urgent NO — first: Talking with children about epilepsy and seizures p.4
- "he sounds drunk but he hasnt been drinking and his smile is crooked" (searched "he sounds drunk but he hasn been drinking and his smile is crooked") — p 0.347, answer, urgent NO — first: Communication p.2 **off**
- "newborn not breathing after birth blue" — p 0.612, answer, urgent yes, body breathing — first: Newborns Babies and Breastfeeding p.1
- "should i pull the knife out" — p 0.8, answer, urgent yes — first: USMC Winter Survival Course Handbook - Historical p.82 **off**
- "vomit looks like coffee grounds" — p 0.682, answer, urgent yes — first: Belly Pain, Diarrhea, and Worms p.38
- "eye got hit by a firework cant see" (searched "eye got hit by a firework can't see") — p 0.383, answer, urgent NO — first: Problems with the Eyes and Seeing p.9 **off**
- "finger cut off" — p 0.642, answer, urgent yes — first: NEETS Module 19 - Technicians Handbook p.18 **off**
- "the child is drinking the cleaning water" — p 0.892, answer, urgent NO — first: Technical note 5. Emergency treatment of drinking-water at the point of use p.4
- "blu lip baby" — p 0.603, answer, urgent yes — first: Newborns Babies and Breastfeeding p.18
- "sezure" (searched "seizure") — p 0.986, answer, urgent yes, body seizure — first: How to help a person having a seizure p.1
- "siezing" (searched "seizing") — p 0.894, answer, urgent NO — first: Equipment Operator p.363 **off**
- "unconshus man" — p 0.518, answer, urgent NO — first: Practice Using Guides, Charts, and Record Sheets p.16 **off**
- "strock" (searched "stock") — p 0.798, answer, urgent NO — first: MIT Introduction to Algorithms — Problem Set 7 p.6 **off**
- "over dose on xanax" — p 0.557, answer, urgent NO — first: Lifespan Development p.591 **off**
- "poisend" (searched "poised") — p 0.894, answer, urgent NO — first: Principles of Economics 3e p.706 **off**
- "brest pain" (searched "best pain") — p 0.893, answer, urgent yes — first: Belly Pain, Diarrhea, and Worms p.30
- "she is breeding a lot from the leg" — p 0.364, answer, urgent NO — first: Contractures: Limbs That No Longer Straighten p.10 **off**
- "he past out" — p 0.463, answer, urgent NO — first: Writing Guide with Handbook p.720 **off**
- "my baby is chocking on milk" (searched "my baby is choking on milk") — p 0.831, answer, urgent yes, body choking — first: Common Disabilities Present at Birth (cleft lip. extra or joined fingers, incomplete limbs, and arthrogryposis) p.2
- "he is not breading" (searched "he is not breeding") — p 0.745, answer, urgent yes, body breathing — first: Microbiology p.377 **off**
- "SHE CANT FEEL HER LEGS" (searched "SHE CAN'T FEEL HER LEGS") — p 0.386, answer, urgent NO — first: Taking care of your body p.7 **off**
- "nooo she's grey and cold and not answering me pls" (searched "noao she's grey and cold and not answering me plus") — p 0.374, answer, urgent NO — first: Cold Weather Safety p.1 **off**
- "sooo much bloooood" (searched "soo much bloooood") — p 0.376, answer, urgent NO — first: Engineering Aid - Construction Methods and Materials p.172 **off**
- "hes not reponding" (searched "he's not responding") — p 0.408, answer, urgent NO — first: Lifespan Development p.832 **off**
- "she isnt responsive at all" (searched "she isn't responsive at all") — p 0.324, answer, urgent NO — first: Principles of Management p.152 **off**
- "kid aint breathin" (searched "kid ant breathing") — p 0.687, answer, urgent yes, body breathing — first: Helping children through death and grief p.26
- "myboyiscoking" (searched "my boy is cooking") — p 0.459, answer, urgent NO — first: Gender and Health p.25
- "nopulsenobreath" (searched "no pulse no breath") — p 0.787, answer, urgent yes, body breathing/pulse — first: Health care skills p.7
- "heimlich on a baby" — p 0.828, answer, urgent yes — first: How to help a person having a seizure p.9
- "finger sweep babys mouth to get it out" (searched "finger sweep baby mouth to get it out") — p 0.604, answer, urgent yes — first: How to help a person having a seizure p.9
- "killing myself tonight" — p 0.342, answer, urgent NO — first: Winter Spotter Training p.14 **off**
- "leaking fluid 30 weeks" — p 0.435, answer, urgent NO — first: NASA Human Integration Design Handbook, Revision 1 p.110 **off**
- "pregnat and having a seizure" (searched "pregnant and having a seizure") — p 0.948, answer, urgent yes, body seizure — first: How to help a person having a seizure p.10
- "ma tête tourne et je vois flou soudain" — p 0.355, answer, urgent NO — first: California Air Tools8010 Air Compressor Owner Manual p.28 **off**
- "shes away with the fairies and talking gibberish" (searched "she's away with the dairies and talking gibberish") — p 0.334, answer, urgent NO — first: Talking with children about epilepsy and seizures p.4

### hybrid: red lines that get the bare "help me help you" (ask, no answer, pages only as consulted) — 4

- "911" — p 0.926, ask, urgent NO, route noise
- "hemmorage" — p 0.2, ask, urgent NO
- "sooo much bloooood" (searched "soo much bloooood") — p 0.225, ask, urgent NO
- "he dropped like a stone in the middle of football" — p 0.249, ask, urgent NO

### hybrid: red lines whose pages are withheld — 4 (the same lines: every withheld red line is a bare ask)

### hybrid: red lines given pages without an answer (ask+pages, UNSURE_DANGER) — 1

- "pleaseeee helpppp my babyy" (searched "pleaseeee helpppp my baby") — p 0.2, ask+pages, urgent yes

### hybrid: red lines judged "sure" (answered, no buttons) whose first page is not from an emergency/first-aid book — 110 of 212 sure red lines; 59 of them with a title that doesn't even look like health (marked **off**)

- "she isnt braething what do i do" (searched "she isn't breathing what do i do") — p 0.706, answer, urgent yes, body breathing — first: Newborns Babies and Breastfeeding p.3
- "help blood" — p 0.947, answer, urgent yes, body bleeding — first: FAO Primary Animal Health Care Worker Manual - Chapter 9: Treating sick animals in general p.4
- "bleeing from head wont stop" (searched "bleeding from head won't stop") — p 0.751, answer, urgent yes, body bleeding — first: NEETS Module 19 - Technicians Handbook p.15 **off**
- "my kid ate one of those little round batteries from the remote" — p 0.618, answer, urgent yes — first: Honda Civic Sedan Owner Manual 2024 p.687 **off**
- "no pulse" — p 0.881, answer, urgent yes, body pulse — first: NEETS Module 12 - Modulation Principles p.157 **off**
- "baby limp and wont feed" (searched "baby limp and won't feed") — p 0.762, answer, urgent yes, body not moving — first: Newborns Babies and Breastfeeding p.2
- "having a fit" — p 0.799, answer, urgent yes, body seizure — first: Lifespan Development p.212 **off**
- "put something in his mouth so he doesnt swallow his tongue??" (searched "put something in his mouth so he doesn't swallow his tongue??") — p 0.741, answer, urgent yes — first: Feeding p.10 **off**
- "toddler had a febrile seizure 2 min stopped now sleepy" — p 0.748, answer, urgent yes, body seizure — first: BEC Transfer and Handover p.None **off**
- "chest pain" — p 0.99, answer, urgent yes, body chest pain — first: Heart Disease and High Blood Pressure p.18
- "sharp pain in chest when i breath in, had a long flight yesterday" — p 0.795, answer, urgent yes, body breathing — first: Download the Pilot's Handbook of Aeronautical Knowledge — Pilot’s Handbook of Aeronautical Knowledge, FAA-H-8083-25C (Full Version) p.441 **off**
- "mum suddenly cant lift her right arm and talking funny" (searched "mum suddenly can't lift her right arm and talking funny") — p 0.484, answer, urgent NO — first: Paralysis p.13 **off**
- "he sounds drunk but he hasnt been drinking and his smile is crooked" (searched "he sounds drunk but he hasn been drinking and his smile is crooked") — p 0.36, answer, urgent NO — first: Front Matter Credits, How to Use This Book, Table of Contents, Introduction p.14 **off**
- "worst headache of my life came on like a thunderclap" — p 0.44, answer, urgent NO — first: Psychology 2e p.523 **off**
- "lips swelling up after peanuts" — p 0.806, answer, urgent yes — first: BEC Breathing p.None
- "stung by a bee now hes wheezing and covered in hives" (searched "stung by a bee now he's wheezing and covered in hives") — p 0.641, answer, urgent yes — first: Good Beekeeping Practices for Sustainable Apiculture p.67 **off**
- "tongue feels huge and itchy after new medicine" — p 0.609, answer, urgent yes — first: Belly Pain, Diarrhea, and Worms p.43
- "electric shock from the socket and now hes not moving" (searched "electric shock from the socket and now he's not moving") — p 0.66, answer, urgent yes, body not moving — first: College Physics 2e p.913 **off**
- "acid on his face from a battery" — p 0.773, answer, urgent yes — first: Storage Battery Maintenance and Principles, April 2020 p.14 **off**
- "kid was under the bath water how long dont know coughing now" (searched "kid was under the bath water how long don't know coughing now") — p 0.698, answer, urgent NO — first: Caring for Children p.16
- "she ate some of grans pills dont know how many" (searched "she ate some of grams pills don't know how many") — p 0.763, answer, urgent yes — first: Medicines for epilepsy and seizures p.5
- "he took a whole box of paracetamol but he says he feels fine" — p 0.482, answer, urgent NO — first: Lifespan Development p.791 **off**
- "she stopped shivering but shes still ice cold and sleepy" (searched "she stopped shivering but she's still ice cold and sleepy") — p 0.764, answer, urgent yes — first: USMC Winter Survival Course Handbook - Historical p.130 **off**
- "my wife is pushing the head is out what do i do" — p 0.796, answer, urgent yes — first: Pregnancy and Birth p.17
- "pregnant bad headache and seeing flashing lights swollen face" — p 0.885, answer, urgent yes — first: Pregnancy and Birth p.7
- "baby hasnt moved all day 36 weeks" (searched "baby hasn moved all day 36 weeks") — p 0.603, answer, urgent yes — first: Pregnancy and Birth p.12
- "gave birth an hour ago bleeding loads soaking pads" — p 0.746, answer, urgent yes, body bleeding — first: Pregnancy and Birth p.27
- "pregnant and one sided stabbing pain and shoulder tip pain feel faint" — p 0.756, answer, urgent yes — first: Belly Pain, Diarrhea, and Worms p.10
- "newborn not breathing after birth blue" — p 0.96, answer, urgent yes, body breathing — first: Newborns Babies and Breastfeeding p.1
- "my baby stopped breathing for a few seconds while sleeping then started again" — p 0.785, answer, urgent yes, body breathing — first: Newborns Babies and Breastfeeding p.12
- "baby breathing really fast and sucking in under ribs" — p 0.608, answer, urgent yes, body breathing — first: Sphere Handbook - Humanitarian Charter and Minimum Standards in Humanitarian Response p.367 **off**
- "baby soft spot sunken and no wet nappy since morning" — p 0.846, answer, urgent yes — first: Newborns Babies and Breastfeeding p.17
- "my son wont stop crying and his tummy is hard and he pulls his legs up and theres red jelly poo" (searched "my son won't stop crying and his tummy is hard and he pulls his legs up and theres red jelly poor") — p 0.452, answer, urgent NO — first: Looking at How Human Relations Affect Health p.3
- "my grandpa is very confused and his sugar is 2.1" — p 0.742, answer, urgent yes — first: Diabetes p.31 **off**
- "breathing like a fish out of water" — p 0.729, answer, urgent yes, body breathing — first: Small-scale Aquaponic Food Production p.126 **off**
- "stridor croup barky cough 3am" (searched "stridor croup bark cough 3am") — p 0.864, answer, urgent NO — first: MSF Measles 2025 EN p.87 **off**
- "stabbed in stomach" — p 0.662, answer, urgent yes — first: Belly Pain, Diarrhea, and Worms p.9
- "knife wound chest bubbling" — p 0.794, answer, urgent yes — first: BEC Penetrating Injury p.None
- "should i pull the knife out" — p 0.946, answer, urgent yes — first: How to sharpen a knife for preppers p.2 **off**
- "throwing up blood" — p 0.753, answer, urgent yes, body bleeding — first: BEC Shock p.None
- "vomit looks like coffee grounds" — p 0.643, answer, urgent yes — first: Belly Pain, Diarrhea, and Worms p.25
- "sudden pain in testicle swollen 14 year old" — p 0.736, answer, urgent yes — first: Painful Joints (includes Medicines for Pain) p.3
- "my friend texted goodbye and wont answer" (searched "my friend tested goodbye and won't answer") — p 0.503, answer, urgent NO — first: UNICEF School-in-a-Box Education Kit Handbook - English (pdf, 2 MB) p.48 **off**
- "eye got hit by a firework cant see" (searched "eye got hit by a firework can't see") — p 0.576, answer, urgent NO — first: Problems with the Eyes and Seeing p.9 **off**
- "sudden blind in one eye like a curtain" — p 0.657, answer, urgent NO — first: Problems with the Eyes and Seeing p.8 **off**
- "crush injury hand in machine" — p 0.764, answer, urgent yes — first: BEC Trauma p.None
- "finger cut off" — p 0.941, answer, urgent yes — first: NEETS Module 19 - Technicians Handbook p.18 **off**
- "put the finger in ice water?" — p 0.676, answer, urgent yes — first: FM 21-76 U.S. Army Survival Manual - Historical p.159 **off**
- "old lady on the floor in the shop wont answer me" (searched "old lady on the floor in the shop won't answer me") — p 0.377, answer, urgent NO — first: Organizing for disability-friendly health care p.15
- "let him sleep it off hes really drunk and cant stand" (searched "let him sleep it off he's really drunk and can't stand") — p 0.338, answer, urgent NO — first: Front Matter Credits, How to Use This Book, Table of Contents, Introduction p.14 **off**
- "im havin a strok i think" (searched "im having a stroke i think") — p 0.652, answer, urgent yes — first: Heart Disease and High Blood Pressure p.20
- "breathin weird" (searched "breathing weird") — p 0.844, answer, urgent yes, body breathing — first: BEC Breathing p.None
- "cant breath" (searched "can't breath") — p 0.62, answer, urgent yes, body breathing — first: Writing Guide with Handbook p.566 **off**
- "she cant breathe properly and her lips are going white" (searched "she can't breathe properly and her lips are going white") — p 0.647, answer, urgent yes, body breathing — first: Writing Guide with Handbook p.539 **off**
- "baby very hot and not eat and sleep sleep all time" — p 0.713, answer, urgent yes — first: How to keep children healthy p.23
- "the child is drinking the cleaning water" — p 0.785, answer, urgent NO — first: UNICEF School-in-a-Box Education Kit Handbook - English (pdf, 2 MB) p.85 **off**
- "my father the sugar he is low low, he no answer" — p 0.687, answer, urgent yes — first: Diabetes p.31 **off**
- "ambulence how" (searched "ambulance how") — p 0.928, answer, urgent yes — first: Emergency Response Plan for Businesses p.5
- "blu lip baby" — p 0.701, answer, urgent yes — first: Newborns Babies and Breastfeeding p.7
- "sezure" (searched "seizure") — p 0.989, answer, urgent yes, body seizure — first: Glossary: Words related to epilepsy p.1
- "siezing" (searched "seizing") — p 0.922, answer, urgent NO — first: Equipment Operator p.363 **off**
- "unconshus man" — p 0.332, answer, urgent NO — first: Sexual health p.5
- "hart attack" — p 0.682, answer, urgent yes — first: Introduction to Computer Science p.891 **off**
- "strock" (searched "stock") — p 0.969, answer, urgent NO — first: Logistics Cluster — Complete Logistics Operational Guide p.222 **off**
- "over dose on xanax" — p 0.661, answer, urgent NO — first: Medicines for epilepsy and seizures p.14
- "poisend" (searched "poised") — p 0.543, answer, urgent NO — first: Libro de cuentos de ¡Prepárate con Pedro! sobre tormentas invernales p.2 **off**
- "brest pain" (searched "best pain") — p 0.728, answer, urgent yes — first: Taking care of your body p.36 **off**
- "cheat pain" — p 0.717, answer, urgent yes — first: Belly Pain, Diarrhea, and Worms p.14
- "she is breeding a lot from the leg" — p 0.437, answer, urgent NO — first: FAO Primary Animal Health Care Worker Manual - Chapter 7: Camels, llamas and alpacas p.2
- "he past out" — p 0.669, answer, urgent NO — first: Introductory Statistics 2e p.560 **off**
- "my baby is chocking on milk" (searched "my baby is choking on milk") — p 0.731, answer, urgent yes, body choking — first: Feeding p.4 **off**
- "he cant breed" (searched "he can't breed") — p 0.499, answer, urgent NO — first: Small-scale Poultry Production p.61 **off**
- "hes not braking" (searched "he's not braking") — p 0.633, answer, urgent yes — first: Honda Civic Sedan Owner Manual 2024 p.525 **off**
- "he is not breading" (searched "he is not breeding") — p 0.873, answer, urgent yes, body breathing — first: MIT Genetics — ps_2001 p.2 **off**
- "my son is having a sea sure" — p 0.303, answer, urgent NO — first: Boat Crew Handbook - Rescue and Survival Procedures (2017) p.2 **off**
- "wont stop bleding from wrist" (searched "won't stop bleeding from wrist") — p 0.616, answer, urgent yes, body bleeding — first: NEETS Module 19 - Technicians Handbook p.15 **off**
- "SHE CANT FEEL HER LEGS" (searched "SHE CAN'T FEEL HER LEGS") — p 0.566, answer, urgent NO — first: Taking care of your body p.7 **off**
- "hes not reponding" (searched "he's not responding") — p 0.578, answer, urgent NO — first: Logistics Cluster — Complete Logistics Operational Guide p.535 **off**
- "she isnt responsive at all" (searched "she isn't responsive at all") — p 0.319, answer, urgent NO — first: Introduction to Part 3: Making Sure Aids and Procedures Do More Good than Harm p.9 **off**
- "my sons lips r blue n he wont wake" (searched "my sons lips r blue n he won't wake") — p 0.665, answer, urgent yes, body unconscious — first: Hearing Loss and Communication p.18 **off**
- "blueslipsandshaking" (searched "blue slips and shaking") — p 0.613, answer, urgent yes — first: Bee Basics: An Introduction to Our Native Bees (2011, USDA Forest Service) p.24 **off**
- "myboyiscoking" (searched "my boy is cooking") — p 0.421, answer, urgent NO — first: Gender and Health p.25
- "bloodwontstop" (searched "blood won't stop") — p 0.715, answer, urgent yes, body bleeding — first: NEETS Module 19 - Technicians Handbook p.15 **off**
- "put him in a cold bath hes overdosed" (searched "put him in a cold bath he's overdose") — p 0.776, answer, urgent yes — first: FM 31-70 Basic Cold Weather Manual - Historical p.178 **off**
- "give her salt water to make her sick she ate pills" — p 0.759, answer, urgent yes — first: Good Food Makes Good Health p.27
- "ok so sorry if this is dumb but my dad keeps saying hes fine but he cant really say words right since lunch and his coffee keeps dribbling out the side of his mouth should i wait for my mum to get home" (searched "ok so sorry if this is dumb but my dad keeps saying he's fine but he can't really say words right since lunch and his coffee keeps dribbling out the side of his mouth should i wait for my mum to get home") — p 0.463, answer, urgent NO — first: Children as Health Workers p.21
- "my daughter is 4 and she had a cold for a few days which was fine but tonight shes breathing really fast and her tummy is going in and out a lot and she doesnt want her cartoons which isnt like her at all" (searched "my daughter is 4 and she had a cold for a few days which was fine but tonight she's breathing really fast and her tummy is going in and out a lot and she doesn't want her cartoons which isn't like her at all") — p 0.615, answer, urgent yes, body breathing — first: Ways to Get People Thinking and Acting Village Theater and Puppet Shows p.4 **off**
- "my neighbour is old and lives alone, i havent seen her for 2 days, i looked through the window and shes on the kitchen floor and moving her hand a bit" (searched "my neighbour is old and lives alone, i haven seen her for 2 days, i looked through the window and she's on the kitchen floor and moving her hand a bit") — p 0.35, answer, urgent NO — first: Lifespan Development p.847 **off**
- "dying to know how to stop this bleeding its everywhere" — p 0.789, answer, urgent yes, body bleeding — first: NEETS Module 19 - Technicians Handbook p.15 **off**
- "bad breath and now he cant breathe at all" (searched "bad breath and now he can't breathe at all") — p 0.671, answer, urgent yes, body breathing — first: BEC Breathing p.None
- "had a fit laughing then actually had a seizure" — p 0.757, answer, urgent yes, body seizure — first: Types of seizures and how to identify them p.5
- "killing myself tonight" — p 0.424, answer, urgent NO — first: Mental health p.7
- "im fine dont worry just cant feel the left side of my body" (searched "im fine don't worry just can't feel the left side of my body") — p 0.463, answer, urgent NO — first: Mental health during different times of life p.20
- "she is ok i think she just took 20 of her sleeping tablets to rest" — p 0.412, answer, urgent NO — first: Acting against epilepsy stigma p.4
- "grandma keeps falling asleep in the chair more than usual and is hard to rouse" — p 0.325, answer, urgent NO — first: Decisions about Special Seats and Wheelchairs p.3 **off**
- "baby crying nonstop for 3 hours high pitched" — p 0.615, answer, urgent yes — first: Lifespan Development p.130 **off**
- "baby got a bump on head and a squishy swelling" (searched "baby got a bump on head and a squash swelling") — p 0.702, answer, urgent yes — first: Newborns Babies and Breastfeeding p.7
- "leaking fluid 30 weeks" — p 0.681, answer, urgent NO — first: Staying healthy p.14
- "pregnat and having a seizure" (searched "pregnant and having a seizure") — p 0.957, answer, urgent yes, body seizure — first: Pregnancy p.23
- "baby born but placenta not out and lots of blood" — p 0.794, answer, urgent yes, body bleeding — first: Pregnancy and Birth p.27
- "paint thinner splashed in my eyes burning" — p 0.674, answer, urgent yes — first: Opticalman 3 and 2 p.169 **off**
- "rash all over after starting new tablets and blisters in mouth" — p 0.628, answer, urgent yes — first: Newborns Babies and Breastfeeding p.24
- "ma tête tourne et je vois flou soudain" — p 0.504, answer, urgent NO — first: The American Printer - A Manual of Typography p.119 **off**
- "my wife pregnant 8 month, much water coming" — p 0.64, answer, urgent yes — first: Practice Using Guides, Charts, and Record Sheets p.15 **off**
- "dady not waking up from nap and breathing slow" (searched "day not waking up from nap and breathing slow") — p 0.607, answer, urgent yes, body breathing/unconscious — first: Living well with epilepsy p.34
- "he's out cold on the pavement after the fight" — p 0.552, answer, urgent NO — first: FM 31-70 Basic Cold Weather Manual - Historical p.178 **off**
- "she keeled over" (searched "she peeled over") — p 0.424, answer, urgent NO — first: Writing Guide with Handbook p.540 **off**
- "shes away with the fairies and talking gibberish" (searched "she's away with the dairies and talking gibberish") — p 0.301, answer, urgent NO — first: Children as Health Workers p.18
- "he's breathing but only like 4 times a minute" — p 0.674, answer, urgent yes, body breathing — first: Health care skills p.7
- "my baby stopped breathing in the car seat and went blue then started again" — p 0.826, answer, urgent yes, body blue/breathing — first: Newborns Babies and Breastfeeding p.3

## Appendix B: typo, glued and real-word-typo lines (keyword run; correction is the same in both modes)

| status | typed | searched | meaning | urgent | body |
|---|---|---|---|---|---|
| wrong word | siezing | seizing | Having a seizure. | NO | - |
| wrong word | strock | stock | Stroke. | NO | - |
| wrong word | poisend | poised | Poisoned. | NO | - |
| wrong word | brest pain | best pain | Chest pain (typed as breast). | yes | - |
| wrong word | hes bleating badly | he's beating badly | He is bleeding badly. | yes | breathing |
| wrong word | he is not breading | he is not breeding | He is not breathing. | yes | breathing |
| wrong word | seasure wont stop | measure won't stop | Seizure won't stop. | yes | seizure |
| wrong word | he is bluding from the hed | he is blading from the head | He is bleeding from the head. | yes | bleeding |
| wrong word | hesss not breeeathing | hess not breathing | He is not breathing. | yes | breathing |
| wrong word | sooo much bloooood | soo much bloooood | So much blood. | NO | - |
| wrong word | nto breathign | onto breathing | Not breathing. | yes | breathing |
| wrong word | blueslipsandshaking | blue slips and shaking | Blue lips and shaking. | yes | - |
| wrong word | myboyiscoking | my boy is cooking | My boy is choking. | NO | - |
| wrong word | facedroopingslurring | face drooping slurry ing | Face drooping and slurring. | yes | - |
| wrong word | dady not waking up from nap and breathing slow | day not waking up from nap and breathing slow | Daddy won't wake from his nap and is breathing slowly. | yes | breathing/unconscious |
| left as typed | hlep | = | Help. | NO | - |
| left as typed | blu lip baby | = | Baby has blue lips. | yes | - |
| left as typed | noo breath | = | Not breathing. | yes | breathing |
| left as typed | anafilactic shock | = | Anaphylactic shock. | yes | - |
| left as typed | unconshus man | = | Unconscious man. | NO | - |
| left as typed | hemmorage | = | Haemorrhage (heavy bleeding). | NO | - |
| left as typed | hart attack | = | Heart attack. | yes | - |
| left as typed | over dose on xanax | = | Overdose on Xanax. | NO | - |
| left as typed | cheat pain | = | Chest pain (typo). | yes | - |
| left as typed | chest pane | = | Chest pain. | yes | - |
| left as typed | she is breeding a lot from the leg | = | She is bleeding a lot from her leg. | NO | - |
| left as typed | he past out | = | He passed out. | NO | - |
| left as typed | he cant breed | he can't breed | He can't breathe (typo). | NO | - |
| left as typed | hes not braking | he's not braking | He is not breathing (autocorrect). | yes | - |
| left as typed | she is not breaking | = | She is not breathing (autocorrect error). | yes | - |
| left as typed | my son is having a sea sure | = | My son is having a seizure. | NO | - |
| left as typed | his face is dropping | = | His face is drooping. | yes | - |
| left as typed | pulse is week and fast | = | Pulse is weak and fast (shock). | yes | pulse |
| left as typed | hes having a heart attach | he's having a heart attach | He is having a heart attack. | yes | - |
| partly fixed | stroke symptons face dropping | stroke symptoms face dropping | Stroke symptoms, face drooping. | yes | - |
| partly fixed | pleaseeee helpppp my babyy | pleaseeee helpppp my baby | Please help my baby (no details; assume serious). | yes | - |
| fixed | HESNOTBREATHING | HE'S NOT BREATHING | He is not breathing. | yes | breathing |
| fixed | she isnt braething what do i do | she isn't breathing what do i do | She is not breathing; what should I do? | yes | breathing |
| fixed | bleeing from head wont stop | bleeding from head won't stop | Bleeding from the head that will not stop. | yes | bleeding |
| fixed | should i put a tournaquet on or just press | should i put a tourniquet on or just press | Should I apply a tourniquet or just press on the wound? (heavy limb bleeding implied) | NO | - |
| fixed | chocking cant breath | choking can't breath | Someone is choking and cannot breathe. | yes | breathing/choking |
| fixed | cant find a puls on her neck | can't find a pulse on her neck | I cannot find a pulse on her neck. | yes | pulse |
| fixed | no hartbeat what do | no heartbeat what do | No heartbeat, what should I do? | yes | pulse |
| fixed | should i give him an asprin hes got chest pain | should i give him an aspirin he's got chest pain | Should I give him aspirin? He has chest pain. | yes | chest pain |
| fixed | slured speach and dizzy all of a suddon | slurred speech and dizzy all of a sudden | Sudden slurred speech and dizziness. | yes | - |
| fixed | rash after amoxicilin no breathing problem | rash after amoxicillin no breathing problem | Rash after amoxicillin, no breathing problems (mild allergy; needs advice soon). | yes | breathing |
| fixed | pregant cant keep water down 2 days | pregnant can't keep water down 2 days | Pregnant and unable to keep water down for 2 days (dehydration risk). | yes | - |
| fixed | babby not braething | baby not breathing | Baby not breathing. | yes | breathing |
| fixed | toddler vomitng and diahrea all day but drinking a bit | toddler vomiting and diarrhea all day but drinking a bit | Toddler vomiting and has diarrhoea all day but drinking some (watch for dehydration). | yes | - |
| fixed | give her sugar she is unconsious diabetic | give her sugar she is unconscious diabetic | Should I give sugar to my unconscious diabetic friend? (Not by mouth if unconscious.) | yes | unconscious |
| fixed | i think im having a heart atack | i think im having a heart attack | I think I am having a heart attack. | yes | - |
| fixed | im havin a strok i think | im having a stroke i think | I think I'm having a stroke. | yes | - |
| fixed | heart attak symtoms woman | heart attack symptoms woman | What are heart attack symptoms in women? (could be informational or current symptoms; treated as urgent) | yes | - |
| fixed | he isnt breathing properley and his chest isnt moving | he isn't breathing properly and his chest isn't moving | He is not breathing properly and his chest isn't moving. | yes | breathing/not moving |
| fixed | breathin weird | breathing weird | Breathing strangely. | yes | breathing |
| fixed | emergancy | emergency | Emergency (no details). | yes | - |
| fixed | ambulence how | ambulance how | How do I get an ambulance? (implies an emergency) | yes | - |
| fixed | sezure | seizure | Seizure. | yes | seizure |
| fixed | anaphalaxis | anaphylaxis | Anaphylaxis. | yes | - |
| fixed | unconcious | unconscious | Unconscious. | yes | unconscious |
| fixed | diahrrea | diarrhea | Diarrhoea (no other details). | NO | - |
| fixed | pnemonia | pneumonia | Pneumonia (question about pneumonia; not clearly an emergency). | NO | - |
| fixed | asma attack | asthma attack | Asthma attack. | yes | - |
| fixed | cholking | choking | Choking. | yes | choking |
| fixed | drowing | drowning | Drowning. | yes | - |
| fixed | overdoes | overdose | Overdose. | yes | - |
| fixed | my baby is chocking on milk | my baby is choking on milk | My baby is choking on milk. | yes | choking |
| fixed | wont stop bleding from wrist | won't stop bleeding from wrist | Won't stop bleeding from the wrist. | yes | bleeding |
| fixed | cant wkae him up | can't wake him up | Can't wake him up. | yes | - |
| fixed | hes not reponding | he's not responding | He is not responding. | NO | - |
| fixed | chokign | choking | Choking. | yes | choking |
| fixed | bledding alot | bleeding lot | Bleeding a lot. | yes | bleeding |
| fixed | cantbreathe | can't breathe | Can't breathe. | yes | breathing |
| fixed | babynotbreathing | baby not breathing | Baby not breathing. | yes | breathing |
| fixed | helpheswontwakeup | help he's won't wake up | Help, he won't wake up. | yes | unconscious |
| fixed | chestpainleftarm | chest pain left arm | Chest pain with left arm pain. | yes | chest pain |
| fixed | sheshavingafit | she's having a fit | She's having a fit. | yes | seizure |
| fixed | nopulsenobreath | no pulse no breath | No pulse, no breathing. | yes | breathing/pulse |
| fixed | bloodwontstop | blood won't stop | Blood won't stop. | yes | bleeding |
| fixed | cellulitus red hot leg spreading | cellulitis red hot leg spreading | Red hot spreading leg (cellulitis). | NO | - |
| fixed | pregnat and having a seizure | pregnant and having a seizure | Pregnant woman having a seizure (eclampsia). | yes | seizure |
| nothing to fix | he swallowed a coin i think he coughing alot but breathing | he swallowed a coin i think he coughing lot but breathing | He may have swallowed a coin; he is coughing a lot but still breathing (partial obstruction - encourage coughing, more urgent if it stops). | yes | breathing |
| nothing to fix | cant breath | can't breath | I can't breathe. | yes | breathing |
| nothing to fix | stomache ache | stomach ache | Stomach ache. | NO | - |

## Appendix C: miss themes, every line

### Red/yellow lines with any detection miss (not urgent, a covered body sign missed, or red pages withheld in either mode) — 126

- **unconscious euphemisms (slumped, out cold, on the floor, won't answer, hard to rouse)** (17): "grandpa fell over in the garden snoring loud cant wake him" / "he turned a funny colour and slumped" / "found him face down in the pond" / "old lady on the floor in the shop wont answer me" / "my nan is on the floor and she cant get up but shes talking" / "my husband he fall and no speak no move" / "my father the sugar he is low low, he no answer" / "I THINK SHES DEAD" / "nooo she's grey and cold and not answering me pls" / "cant wkae him up" / "she isnt responsive at all" / "pour water on his face to wake him up" / "my neighbour is old and lives alone, i havent seen her for 2 days, i looked through the window and shes on the kitchen floor and moving her hand a bit" / "grandma keeps falling asleep in the chair more than usual and is hard to rouse" / "my wife is fainting and i am alone with kids what i do" / "he's out cold on the pavement after the fight" / "he dropped like a stone in the middle of football"
- **real-word autocorrect / real-word typo (breeding, breaking, sea sure, past out)** (13): "strock" / "poisend" / "brest pain" / "cheat pain" / "chest pane" / "she is breeding a lot from the leg" / "he past out" / "he cant breed" / "hes not braking" / "she is not breaking" / "my son is having a sea sure" / "myboyiscoking" / "she keeled over"
- **misspelling the corrector left or bent** (10): "should i put a tournaquet on or just press" / "blu lip baby" / "siezing" / "unconshus man" / "hemmorage" / "pnemonia" / "sooo much bloooood" / "hes not reponding" / "blueslipsandshaking" / "cellulitus red hot leg spreading"
- **bleeding wordings without blood/bleed (pouring, oozing, cut off, shot)** (10): "i think his leg is broken bone sticking out" / "he got shot in the leg" / "heavy period soaking pad every hour dizzy" / "vomit looks like coffee grounds" / "nosebleed wont stop for 30 min" / "i cut myself deep and it wont stop" / "finger cut off" / "the dog is fine but my son got bitten on the neck and its pouring" / "sliced palm deep can see white stuff" / "my 85 year old father has a cut on his shin that wont stop oozing he takes warfarin"
- **yellow conditions with no urgent word (fracture, tooth, urine, infection, object)** (10): "my 2 yr old put a bead up her nose" / "cant pee at all since yesterday belly swollen" / "cat scratch on hand now swollen and red" / "mum dementia hasnt peed all day" / "my leg is swollen and hot after the operation" / "erection lasting 5 hours" / "knocked out tooth adult put back?" / "how do u know if u broke ur arm" / "ankle crunched when i landed and now i cant stand on it at all" / "broke my nose i think its bent"
- **chest pain / heart wordings (elephant, tight chest, heart racing)** (9): "i cant feel his heart beating" / "feels like an elephant sitting on my chest and im sweating" / "tight chest jaw ache feel sick 58 m" / "heart racing like crazy wont slow down feel faint" / "my mother she have pain in heart very strong and sweat" / "her heart is beating really slow like 30" / "heimlich on a baby" / "idk whats happening my boyfriend took something at a festival and hes super hot and his jaw is clenching and hes not making sense anymore and his heart is going so fast" / "hes having a heart attack i think he's 70 and on the floor not talking"
- **stroke words (face, arm, speech, one side, vision)** (9): "mum suddenly cant lift her right arm and talking funny" / "he sounds drunk but he hasnt been drinking and his smile is crooked" / "sudden blind in one eye like a curtain" / "so like i was at my cousins bbq and my uncle had a few beers and then he just kind of sat down weird and now hes sweating heaps and saying his arm feels heavy and everyone says its the heat but i dunno" / "ok so sorry if this is dumb but my dad keeps saying hes fine but he cant really say words right since lunch and his coffee keeps dribbling out the side of his mouth should i wait for my mum to get home" / "im fine dont worry just cant feel the left side of my body" / "had a funny turn" / "my gran's come over all peculiar" / "shes away with the fairies and talking gibberish"
- **overdose / poisoning without the word** (8): "he took a whole box of paracetamol but he says he feels fine" / "took 2 extra panadol by mistake" / "he fell asleep drunk on his back and being sick" / "let him sleep it off hes really drunk and cant stand" / "the child is drinking the cleaning water" / "over dose on xanax" / "she is ok i think she just took 20 of her sleeping tablets to rest" / "my nan swallowed her denture plate i think shes coughing"
- **seizure slang (fitting, shaking, eyes rolling, tongue)** (7): "shes fitting and wont stop been 6 minutes" / "he is shaking all over on the floor and foam from mouth" / "put something in his mouth so he doesnt swallow his tongue??" / "my baby is hot and shaking and his eyes rolled back" / "HELP ME HES SHAKING AND HIS EYES ARE ROLLING" / "he swallowed his tongue" / "im 10 and my mom is shaking on the floor"
- **other** (5): "hlep" / "helo my son" / "911" / "we were hiking and my wife slipped on the rocks and hit her head she was out for maybe a minute and now shes awake but keeps asking the same questions over and over" / "the old man fall in the bath, he is cold and talk little"
- **CPR named, no body word (body_signs only)** (3): "how do i do cpr on a man" / "how many pushes for cpr baby" / "cpr on dog or person same?? my husband"
- **suicide / self-harm euphemisms** (3): "my friend texted goodbye and wont answer" / "killing myself tonight" / "i want to disappear forever"
- **cold / heat exposure** (2): "should i rub his hands and give him brandy hes frozen" / "bit dizzy and headache in the heat drinking water now"
- **pregnancy / birth** (2): "spotting at 7 weeks with cramps" / "leaking fluid 30 weeks"
- **agonal / noisy breathing (snoring, gurgling, stridor)** (2): "stridor croup barky cough 3am" / "she's gurgling"
- **first-aid misconception (venom, finger sweep)** (2): "should i suck the venom out" / "finger sweep babys mouth to get it out"
- **eye injury** (2): "eye got hit by a firework cant see" / "something in my eye wont come out and its scratching"
- **non-English** (2): "mi esposa no respira help" / "ma tête tourne et je vois flou soudain"
- **blue alone ("hes blue")** (2): "hes blue" / "it was a blue screen but now my brother is blue"
- **limb / circulation (can't feel legs, tight cast)** (2): "SHE CANT FEEL HER LEGS" / "cast feels super tight toes going cold"
- **severe headache** (1): "worst headache of my life came on like a thunderclap"
- **allergy / anaphylaxis words** (1): "throat closing up ate shrimp"
- **drowning / submersion without the word** (1): "kid was under the bath water how long dont know coughing now"
- **child/baby specific (red jelly poo)** (1): "my son wont stop crying and his tummy is hard and he pulls his legs up and theres red jelly poo"
- **breathing difficulty words (asthma, inhaler)** (1): "asthma attack inhaler not working"
- **colour words (grey, ash, funny colour)** (1): "she is not good, colour is like ash"

### Red lines not urgent (is_danger false) — 50

- **unconscious euphemisms (slumped, out cold, on the floor, won't answer, hard to rouse)** (8): "he turned a funny colour and slumped" / "old lady on the floor in the shop wont answer me" / "nooo she's grey and cold and not answering me pls" / "she isnt responsive at all" / "my neighbour is old and lives alone, i havent seen her for 2 days, i looked through the window and shes on the kitchen floor and moving her hand a bit" / "grandma keeps falling asleep in the chair more than usual and is hard to rouse" / "he's out cold on the pavement after the fight" / "he dropped like a stone in the middle of football"
- **real-word autocorrect / real-word typo (breeding, breaking, sea sure, past out)** (8): "strock" / "poisend" / "she is breeding a lot from the leg" / "he past out" / "he cant breed" / "my son is having a sea sure" / "myboyiscoking" / "she keeled over"
- **stroke words (face, arm, speech, one side, vision)** (7): "mum suddenly cant lift her right arm and talking funny" / "he sounds drunk but he hasnt been drinking and his smile is crooked" / "sudden blind in one eye like a curtain" / "so like i was at my cousins bbq and my uncle had a few beers and then he just kind of sat down weird and now hes sweating heaps and saying his arm feels heavy and everyone says its the heat but i dunno" / "ok so sorry if this is dumb but my dad keeps saying hes fine but he cant really say words right since lunch and his coffee keeps dribbling out the side of his mouth should i wait for my mum to get home" / "im fine dont worry just cant feel the left side of my body" / "shes away with the fairies and talking gibberish"
- **misspelling the corrector left or bent** (6): "should i put a tournaquet on or just press" / "siezing" / "unconshus man" / "hemmorage" / "sooo much bloooood" / "hes not reponding"
- **overdose / poisoning without the word** (5): "he took a whole box of paracetamol but he says he feels fine" / "let him sleep it off hes really drunk and cant stand" / "the child is drinking the cleaning water" / "over dose on xanax" / "she is ok i think she just took 20 of her sleeping tablets to rest"
- **agonal / noisy breathing (snoring, gurgling, stridor)** (2): "stridor croup barky cough 3am" / "she's gurgling"
- **suicide / self-harm euphemisms** (2): "my friend texted goodbye and wont answer" / "killing myself tonight"
- **limb / circulation (can't feel legs, tight cast)** (2): "SHE CANT FEEL HER LEGS" / "cast feels super tight toes going cold"
- **severe headache** (1): "worst headache of my life came on like a thunderclap"
- **drowning / submersion without the word** (1): "kid was under the bath water how long dont know coughing now"
- **cold / heat exposure** (1): "should i rub his hands and give him brandy hes frozen"
- **child/baby specific (red jelly poo)** (1): "my son wont stop crying and his tummy is hard and he pulls his legs up and theres red jelly poo"
- **first-aid misconception (venom, finger sweep)** (1): "should i suck the venom out"
- **eye injury** (1): "eye got hit by a firework cant see"
- **colour words (grey, ash, funny colour)** (1): "she is not good, colour is like ash"
- **other** (1): "911"
- **pregnancy / birth** (1): "leaking fluid 30 weeks"
- **non-English** (1): "ma tête tourne et je vois flou soudain"

### Yellow lines not urgent — 25

- **yellow conditions with no urgent word (fracture, tooth, urine, infection, object)** (10): "my 2 yr old put a bead up her nose" / "cant pee at all since yesterday belly swollen" / "cat scratch on hand now swollen and red" / "mum dementia hasnt peed all day" / "my leg is swollen and hot after the operation" / "erection lasting 5 hours" / "knocked out tooth adult put back?" / "how do u know if u broke ur arm" / "ankle crunched when i landed and now i cant stand on it at all" / "broke my nose i think its bent"
- **bleeding wordings without blood/bleed (pouring, oozing, cut off, shot)** (3): "heavy period soaking pad every hour dizzy" / "nosebleed wont stop for 30 min" / "sliced palm deep can see white stuff"
- **other** (2): "hlep" / "helo my son"
- **misspelling the corrector left or bent** (2): "pnemonia" / "cellulitus red hot leg spreading"
- **stroke words (face, arm, speech, one side, vision)** (2): "had a funny turn" / "my gran's come over all peculiar"
- **overdose / poisoning without the word** (1): "took 2 extra panadol by mistake"
- **cold / heat exposure** (1): "bit dizzy and headache in the heat drinking water now"
- **pregnancy / birth** (1): "spotting at 7 weeks with cramps"
- **unconscious euphemisms (slumped, out cold, on the floor, won't answer, hard to rouse)** (1): "my nan is on the floor and she cant get up but shes talking"
- **suicide / self-harm euphemisms** (1): "i want to disappear forever"
- **eye injury** (1): "something in my eye wont come out and its scratching"

### Red/yellow lines with a sign body_signs covers, not found — 76

- **unconscious euphemisms (slumped, out cold, on the floor, won't answer, hard to rouse)** (16): "grandpa fell over in the garden snoring loud cant wake him" / "he turned a funny colour and slumped" / "found him face down in the pond" / "old lady on the floor in the shop wont answer me" / "my husband he fall and no speak no move" / "my father the sugar he is low low, he no answer" / "I THINK SHES DEAD" / "nooo she's grey and cold and not answering me pls" / "cant wkae him up" / "she isnt responsive at all" / "pour water on his face to wake him up" / "my neighbour is old and lives alone, i havent seen her for 2 days, i looked through the window and shes on the kitchen floor and moving her hand a bit" / "grandma keeps falling asleep in the chair more than usual and is hard to rouse" / "my wife is fainting and i am alone with kids what i do" / "he's out cold on the pavement after the fight" / "he dropped like a stone in the middle of football"
- **real-word autocorrect / real-word typo (breeding, breaking, sea sure, past out)** (11): "brest pain" / "cheat pain" / "chest pane" / "she is breeding a lot from the leg" / "he past out" / "he cant breed" / "hes not braking" / "she is not breaking" / "my son is having a sea sure" / "myboyiscoking" / "she keeled over"
- **chest pain / heart wordings (elephant, tight chest, heart racing)** (9): "i cant feel his heart beating" / "feels like an elephant sitting on my chest and im sweating" / "tight chest jaw ache feel sick 58 m" / "heart racing like crazy wont slow down feel faint" / "my mother she have pain in heart very strong and sweat" / "her heart is beating really slow like 30" / "heimlich on a baby" / "idk whats happening my boyfriend took something at a festival and hes super hot and his jaw is clenching and hes not making sense anymore and his heart is going so fast" / "hes having a heart attack i think he's 70 and on the floor not talking"
- **bleeding wordings without blood/bleed (pouring, oozing, cut off, shot)** (9): "i think his leg is broken bone sticking out" / "he got shot in the leg" / "heavy period soaking pad every hour dizzy" / "vomit looks like coffee grounds" / "nosebleed wont stop for 30 min" / "i cut myself deep and it wont stop" / "finger cut off" / "the dog is fine but my son got bitten on the neck and its pouring" / "my 85 year old father has a cut on his shin that wont stop oozing he takes warfarin"
- **misspelling the corrector left or bent** (8): "should i put a tournaquet on or just press" / "blu lip baby" / "siezing" / "unconshus man" / "hemmorage" / "sooo much bloooood" / "hes not reponding" / "blueslipsandshaking"
- **seizure slang (fitting, shaking, eyes rolling, tongue)** (7): "shes fitting and wont stop been 6 minutes" / "he is shaking all over on the floor and foam from mouth" / "put something in his mouth so he doesnt swallow his tongue??" / "my baby is hot and shaking and his eyes rolled back" / "HELP ME HES SHAKING AND HIS EYES ARE ROLLING" / "he swallowed his tongue" / "im 10 and my mom is shaking on the floor"
- **CPR named, no body word (body_signs only)** (3): "how do i do cpr on a man" / "how many pushes for cpr baby" / "cpr on dog or person same?? my husband"
- **overdose / poisoning without the word** (2): "he fell asleep drunk on his back and being sick" / "my nan swallowed her denture plate i think shes coughing"
- **blue alone ("hes blue")** (2): "hes blue" / "it was a blue screen but now my brother is blue"
- **other** (2): "we were hiking and my wife slipped on the rocks and hit her head she was out for maybe a minute and now shes awake but keeps asking the same questions over and over" / "the old man fall in the bath, he is cold and talk little"
- **allergy / anaphylaxis words** (1): "throat closing up ate shrimp"
- **child/baby specific (red jelly poo)** (1): "my son wont stop crying and his tummy is hard and he pulls his legs up and theres red jelly poo"
- **breathing difficulty words (asthma, inhaler)** (1): "asthma attack inhaler not working"
- **non-English** (1): "mi esposa no respira help"
- **colour words (grey, ash, funny colour)** (1): "she is not good, colour is like ash"
- **first-aid misconception (venom, finger sweep)** (1): "finger sweep babys mouth to get it out"
- **agonal / noisy breathing (snoring, gurgling, stridor)** (1): "she's gurgling"

## Appendix D: body_signs on green lines (false positives), in full

- "my kid got some hives after strawberries but breathing fine and playing" — breathing (child, mild)
- "my cat is not breathing properly" — breathing (counterexample)
- "nose bleed tilt head back?" — bleeding (misconception, mild)
- "my nose is bleeding a bit after picking it" — bleeding (mild)
- "cut my thumb chopping onions bleeding a bit" — bleeding (mild)
- "bit my tongue its bleeding a little" — bleeding (mild)
- "bad breath" — breathing (counterexample)
- "how to fix bad breath from garlic" — breathing (counterexample)
- "breath of fresh air" — breathing (counterexample, fragment)
- "take a deep breath before the exam tips" — breathing (counterexample)
- "breathing exercises for yoga" — breathing (counterexample)
- "the pulse of the city at night" — pulse (counterexample)
- "pulse lentils recipe" — pulse (counterexample)
- "blend on pulse setting" — pulse (counterexample)
- "bleeding edge tech" — bleeding (counterexample, fragment)
- "the battery is choking on the cold" — choking (counterexample)
- "bleed the radiator" — bleeding (counterexample)
- "blood orange cake" — bleeding (counterexample)
- "black pudding is it blood" — bleeding (counterexample)
- "how to bleed brakes on bike" — bleeding (counterexample)
- "my engine is choking" — choking (counterexample)
- "choke on a motorbike what does it do" — choking (counterexample)
- "the team choked in the final" — choking (counterexample, slang)
- "choked up at the wedding speech" — choking (counterexample)
- "the plant is wilting and looks floppy" — not moving (counterexample)
- "my sourdough starter isnt breathing" — breathing (counterexample, slang)
- "let the wine breathe how long" — breathing (counterexample)
- "fabric that breathes for running" — breathing (counterexample)
- "the dough is bleeding red food colouring" — bleeding (counterexample)
- "colour bleed in the wash pink shirt" — bleeding (counterexample)
- "bleed in printing what is bleed area" — bleeding (counterexample)
- "having a fit about the parking ticket" — seizure (counterexample, slang)
- "seizure of assets by the bank" — seizure (counterexample)
- "he collapsed into laughter" — unconscious (counterexample)
- "the tent collapsed in the wind" — unconscious (counterexample)
- "passed out of the academy" — unconscious (counterexample)
- "the bass line is the heartbeat of the song" — pulse (counterexample)
- "blood brothers musical tickets" — bleeding (counterexample)
- "first blood in the game" — bleeding (counterexample, slang)
- "blue lips lipstick shade" — blue (counterexample)
- "my lips are blue from the slushie" — blue (counterexample)
- "code is bleeding memory leak" — bleeding (counterexample)
- "server has no heartbeat monitoring alert" — pulse (counterexample)
- "my character is bleeding out in the game how to heal" — bleeding (counterexample)
- "how to make fake blood for halloween" — bleeding (counterexample)
- "choking hazard toys age 3" — choking (counterexample, child)
- "what is a seizure" — seizure (counterexample)
- "what is a normal pulse for a 40 year old" — pulse (counterexample)
- "heartbreak hotel chords" — pulse (counterexample)
- "i fainted while giving blood" — bleeding/unconscious (mild)
- "fainted in a hot church standing a long time feel fine now" — unconscious (mild)
- "chapped lips bleeding a little" — bleeding (mild)
- "little cut in my finger, small blood, is ok?" — bleeding (non-native, mild)
- "i fell off my bike and my knee is bleeding but im ok" — bleeding (child, mild)
