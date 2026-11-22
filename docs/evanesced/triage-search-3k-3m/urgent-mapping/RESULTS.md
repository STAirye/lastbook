# Mapping the fork's urgency rules onto #167's `urgent` field

Everything below comes from `measure.py` (run 2026-11-21, output in `measure_out.json`). Proposed phrases: `proposed_urgent.json`.
Nothing tracked was edited, nothing committed, no network, the meaning model was never loaded.

## What #167 does (as it is in the tree)

- A choice lists `urgent` phrases; `web/words.js` `names()` matches each as whole words in order over **all** the search's words
  (stop words too). `splitWords` splits on anything that is not a letter, mark or digit, so `isn't` is `isn` + `t`
  (hence "isn't breathing" and "isnt breathing" are two phrases). A hit makes that choice the topic's choice and lists the topic first,
  even under the 60% cut.
- Only `hurt/breathing` has it, with 5 phrases: not breathing, stopped breathing, isn't breathing, isnt breathing, unconscious.
  The merged commit 33a32d5 listed 8; `e2fa394` later removed "unresponsive", "not responding" and "choking" on purpose
  (they also mean "wound not responding to antibiotics", "allergic reaction choking", "choking on smoke"). Any proposal has to respect that.
- `SCHEMA.md`: `urgent` is "only for a life-threatening choice that must win over any other choice in its topic".
- The Python port of the matching in `measure.py` was checked against the real `web/words.js` run in Node, over all 2,189 lines and both
  phrase sets: **0 disagreements**.

## 1. Inventory of the fork's urgency rules

Counts are top-level alternatives of each regex (the script splits the patterns at depth-0 `|`), or entries of a table.
Kinds: plain = a word or fixed phrase; stem = `word\w*`; optional = regex with optional or alternative words (`can'?t`, `(is|was) ...`);
window = words allowed in between (`.{0,25}`, `(\w+ ){0,4}`).

| Source | Items | plain | stem | optional | window | Role |
|---|---|---|---|---|---|---|
| `assistant.DANGER` (15 named signs) | 40 | 18 | 6 | 14 | 2 | narrow: changes the search (`danger_signs`) |
| `confidence.URGENT` | 275 | 125 | 81 | 67 | 2 | wide net: "never hold the pages back" |
| `confidence.BODY_PHRASES` (9 signs) | 44 | 0 | 6 | 33 | 5 | body signs, with negation/gaps ("won't wake up", "cut ... won't stop") |
| `confidence.BODY_WORDS` | 23 words | 23 | | | | matched with typo slips (1-2 edits, first letter kept) |
| `confidence.BODY_GLUED` | 17 stems | | | | | found inside glued runs ("mybbyisntbreathing") |
| `confidence.NOT_URGENT` | 72 | | | | | idioms cut out before the above ("drowning in homework") |
| `typos` tables | SLIPS 5, PHRASE_SLIPS 12, APOSTROPHES 47 | | | | | plus the algorithmic corrector over the library's own words |
| `engine.meaning_red` | not a phrase list | | | | | embedding vs centroids; only adds urgency |

By category (DANGER and BODY_* are named by the fork; URGENT's categories are a keyword heuristic written in `measure.py`, so treat them as approximate;
the two rows marked * are the generic ones):

| Category | DANGER | BODY_PHRASES | BODY_WORDS | BODY_GLUED | URGENT (heuristic) |
|---|---|---|---|---|---|
| not breathing / airway | 4 (plain 3, stem 1) | 4 (window 2) | 5 | 2 | 7 |
| choking | 1 (optional) | 0 | 4 | 1 | 1 |
| unconscious / collapse / not responding | 4 + 2 "passed out" | 14 (optional 9, stem 5) | 3 | 4 | 20 |
| cardiac / pulse / CPR / heart attack | 2 + 1 | 3 | 3 | 3 | 5 |
| chest pain | 2 | 5 (window 2) | 0 | 1 | 1 |
| bleeding | 6 | 4 (window 1) | 3 | 2 | 20 |
| stroke | 0 | 0 | 0 | 0 | 26 (mostly optional-word regexes) |
| anaphylaxis / allergy / asthma | 0 | 0 | 0 | 0 | 10 |
| overdose / poisoning | 2 (one has a 30-char window) | 0 | 0 | 0 | 30 |
| seizure | 3 | 7 | 4 | 2 | 9 |
| burns / fire / smoke | 3 "on fire" | 0 | 0 | 0 | 9 |
| drowning / water / flood | 2 | 0 | 0 | 0 | 10 |
| gas / CO | 2 "smell gas" | 0 | 0 | 0 | 4 |
| suicide / self-harm | 0 | 0 | 0 | 0 | 15 |
| pregnancy / birth | 0 | 0 | 0 | 0 | 8 |
| hypothermia / heat | 0 | 0 | 0 | 0 | 3 |
| head / spine / fall / crush / trapped | 3 "trapped" | 0 | 0 | 0 | 18 |
| snake bite | 3 | 0 | 0 | 0 | (in bite/sting words) |
| blue lips, cold and clammy, not moving | 0 | 3 + 2 + 2 | 1 | 2 | few |
| generic* (help, pain, pale, weak, ...) / other* | 0 | 0 | 0 | 0 | 43 |
| injury / fracture / disaster / violence / infection / electric | 0 | 0 | 0 | 0 | 14 + 13 + 5 + 4 |

Typo handling is separate from the lists: `typos.correct` (library words, one or two edits), the `BODY_WORDS` slip rule, `BODY_GLUED`, apostrophe repair.
None of it is a phrase.

## 2. Mapping to guides (every `content/topics/*.json` read)

Hurt-first: all the person-in-danger rules map to `hurt`. Proposed phrases are in `proposed_urgent.json` (117 phrases, 16 choices); the table shows the idea.

| Fork category | Guide topic / choice | Proposed `urgent` (whole words, in order, lower case) | Cannot be expressed |
|---|---|---|---|
| not breathing, unconscious, cardiac arrest, collapse, drowning, choking | `hurt/breathing` (label already says "Not breathing, unconscious or choking"; hint lists collapse, cardiac arrest, drowning) | existing 5, plus no pulse, cardiac arrest, heart stopped, cpr, passed out, won't/wont wake up, not waking up, collapsed, drowning, drowned, "is choking" forms | `breath\w*`, "can't breathe" (guide routes it to allergy on purpose), gasping/gurgling/snoring windows, body-word typos, glued words, `unresponsive`/`not responding` (removed upstream) |
| bleeding a lot | `hurt/bleeding` | heavy bleeding, bleeding heavily/badly/a lot, won't stop bleeding, bleeding out, spurting blood, blood everywhere, lots of blood | "pouring/gushing/soaking (through)" lists, "cut ... won't stop" window |
| anaphylaxis | `hurt/allergy` | anaphylaxis, anaphylactic, throat swelling/closing, swollen throat, tongue swelling | "lips swelling" (too broad), "swell\w*" |
| overdose, poisoning | `hurt/poison` | overdose(d), took too many pills, swallowed bleach/poison/pills, was poisoned | `(swallowed\|drank) .{0,30} (bleach\|pills\|...)` window, brand and drug lists (tylenol, xanax, fentanyl...), "whole bottle" forms |
| chest pain, heart attack, stroke, seizure, diabetic | `hurt/sudden` | heart attack, chest pain(s), having/had a stroke, face drooping, slurred speech, seizure(s), having a seizure, convulsions, having a fit | the 26 stroke regexes ("can't lift his arm", "one side of his face"), "elephant on my chest", "eyes rolling", "fitting" typo slips. A bare "stroke" would send "heat stroke" to this choice, so it is not proposed |
| heat stroke, hypothermia | `hurt/heatcold` (and `shelter/heat`, `shelter/cold`) | heat stroke, heatstroke, hypothermia | "hot and confused", "not shivering" |
| snake bite | `hurt/snakebite` | snake bite, snakebite, bitten/bit by a snake, snake bit | "snake .{0,12} bit" window |
| burning clothing | `hurt/burn` | clothes/clothing on fire | "on fire" as a bare phrase (would catch campfire how-tos) |
| fire in a building | `disaster/home-fire` | house fire, house/kitchen/building/apartment is on fire, caught fire, fire in the house | wildfire / smoke family |
| gas leak | `power/gas` | smell gas, smell of gas, smells like gas, gas leak | typo slips ("gas leek") |
| carbon monoxide | `shelter/co` | carbon monoxide poisoning, co poisoning, co alarm going off | bare "carbon monoxide" (generator how-tos) |
| suicide, self-harm | `health/mind` (label: "someone in crisis"; hint: "suicidal") | suicide, suicidal, kill myself, want to die, end my life, take my own life, self harm, hurt myself | slang ("unalive", "kms"), "better off without me", "goodbye" regexes, the meaning check |
| labour, bleeding after birth | `health/pregnant` | in labor/labour, giving birth, water broke, baby is coming, bleeding after birth | "contractions" (also grammar), miscarriage family |
| earthquake / tsunami / tornado now | `disaster/earthquake-now`, `tsunami`, `tornado` | ground is shaking, tsunami warning, tornado warning, ... | (fork has no rule of its own beyond `URGENT` words) |

What the Python side must keep on top of any phrase list: `NOT_URGENT` idiom cutting; typo correction and `BODY_WORDS` slips; `BODY_GLUED`; `can'?t`/apostrophe
variants (words.js already splits `isn't` into two words, so Python and JS should compare the same split); the regexes with windows and optional words;
the wide `URGENT` net (pages never held back); the meaning check (sits beside the phrases as a second, additive vote; it needs no phrase source).

## 3. Gaps both ways

Fork categories with no guide choice to point to (so no `urgent` phrase is possible until a choice exists):
1. **Drowning / stuck in water**, **electric shock / live wire / lightning victim**, **trapped / crush / buried**: only appear in hints (`hurt/breathing` mentions drowning; `hurt/burn` mentions electricity; `hurt/nohelp` mentions earthquake). No choice for them.
2. **Overdose by opioid** (naloxone), **choking** on its own (folded into `breathing`, which upstream chose not to key on "choking"), **asthma attack**, **diabetic emergency** (folded into `sudden`), **eye splash with chemicals**, **croup**, **sepsis / chemo fever**, **vision loss**, **thunderclap headache**, **sudden weakness**: the independent lists have red lines for these; the only hurt choices that could take them are broad ones.
3. **Violence / attack / intruder** (in `URGENT`): no first-aid choice; `disaster/explosion` is the nearest.

Guide choices that look urgent but have no fork rule of their own (the fork only reaches them through the wide `URGENT` words, or the meaning check):
`hurt/shock`, `hurt/head` (head, neck or back injury), `hurt/bone`, `hurt/animal-bite`, `hurt/sting`, `hurt/check`, `hurt/nohelp`,
`disaster/wildfire`, `disaster/explosion`, `disaster/nuclear-explosion`, `disaster/shelter-in-place`, `disaster/highrise-fire`,
`water/chemical`, `shelter/damaged`, `health/teeth` (swollen face / abscess), `health/medicine`.

## 4. Measurement

Lines flagged urgent, by label. Lists: three independent held-out lists (690, 606, 531 lines) and the triage set (`cases.py`: 362 questions, clean plus typo versions).
- (a) #167 phrases as in the tree (5 phrases, Not breathing only).
- (b) the 117 proposed phrases, matched like `words.js` (verified in Node).
- (c) the fork's words alone, no meaning model: `assistant.danger_signs(t) or confidence.urgent(t, typos.correct(t))`, i.e. `is_danger` without the meaning check.
- (d) = (b) or (c). Extra columns: (c1) `danger_signs` alone (the narrow list); (c2) `confidence.urgent` on the text as typed; (e) = (b) after cutting `NOT_URGENT` idioms first.

| list | colour | n | (a) now | (b) proposed | (c) fork | (d) b or c | c1 danger_signs | c2 urgent typed | (e) b with idioms cut |
|---|---|---|---|---|---|---|---|---|---|
| independent | red | 343 | 9 | 49 | 340 | 340 | 59 | 314 | 49 |
| independent | yellow | 104 | 0 | 2 | 98 | 98 | 9 | 94 | 2 |
| independent | green | 243 | 2 | 19 | 76 | 90 | 5 | 76 | 5 |
| independent2 | red | 249 | 8 | 43 | 230 | 231 | 44 | 223 | 43 |
| independent2 | yellow | 111 | 0 | 1 | 85 | 85 | 4 | 85 | 1 |
| independent2 | green | 246 | 3 | 28 | 127 | 133 | 23 | 126 | 22 |
| independent3 | red | 199 | 3 | 20 | 173 | 173 | 26 | 169 | 20 |
| independent3 | yellow | 78 | 0 | 2 | 55 | 55 | 4 | 55 | 2 |
| independent3 | green | 254 | 3 | 32 | 154 | 156 | 31 | 153 | 30 |
| triage | red | 218 | 14 | 53 | 218 | 218 | 50 | 205 | 53 |
| triage | yellow | 74 | 0 | 1 | 59 | 59 | 1 | 54 | 1 |
| triage | green | 70 | 0 | 1 | 38 | 38 | 2 | 37 | 1 |
| **all** | red | 1009 | 34 (3%) | 165 (16%) | 961 (95%) | 962 (95%) | 179 (18%) | 911 | 165 |
| **all** | yellow | 367 | 0 | 6 (2%) | 297 (81%) | 297 | 18 (5%) | 288 | 6 |
| **all** | green | 813 | 8 (1%) | 80 (10%) | 395 (49%) | 417 (51%) | 61 (8%) | 392 | 58 (7%) |

How to read it:
- #167 as it is catches 3% of the red lines; the proposed phrases for all categories catch 16%, about the same as the fork's own **narrow** list (`danger_signs`, 18%). So phrases of #167's kind can do the narrow job, not the wide one.
- The fork's wide check (`URGENT` plus body signs plus typos) is a different thing: 95% of red, but also 49% of green and 81% of yellow. It is meant that way (it only stops pages being held back). It is not a candidate for a "put this guide first" field.
- Typo correction matters: `urgent` typed 911 red, typo-fixed 961.
- (b) adds only 1 red line that the fork's keyword check misses ("his throat is closing after peanuts"); (d) is 962 vs (c) 961.
- Green lines flagged by (b): 80; with idioms cut first (e) 58. What remains is mostly "how do I do CPR", "what is a seizure", "cpr certification" (an information question about an urgent topic) and idioms the idiom list does not cover ("heartbeat endpoint", "my sims baby is not breathing"). The 22 lines idiom-cutting removes are things like "drowning in emails", "overdosed on netflix", "seizure of assets", "the tent collapsed".
- The labelled green/yellow lines include the same people's wording as red ones, so these rates are not a false-alarm rate on real searches.

## 5. Design proposal (for a 5-minute review)

1. **One source of phrases:** the `urgent` arrays already in `content/topics/*.json`. They are the only place phrases are written. Python reads them
   the same way the app does (load the JSON, split with the same rule as `splitWords`: lower case, NFKD, drop Latin marks, split on non letters/marks/digits, match whole words in order).
2. **Python library search adds on top, never replaces:** (a) the phrases from the guides, matched on the typed text and on the typo-corrected text, so "he isnt braething" reaches "isn't breathing"; (b) `NOT_URGENT` idiom cutting before matching; (c) the wide `URGENT`/`BODY_*` words, which are not phrases; (d) the meaning check, still additive. `danger_signs` and `DANGER` would shrink to what phrases cannot say (windows, optional words, slip tables); the plain phrases in `DANGER` ("heart attack", "not breathing", "stopped breathing", "no pulse", "chest pain", "smell gas", "gas leak") move into the guide fields.
3. **Rule for what goes in a guide field:** a multi-word phrase naming a person's state or the event ("having a stroke", "heavy bleeding"), never a bare word with a harmless sense ("stroke", "choking", "unresponsive", "fire", "carbon monoxide"). Upstream's own commit `e2fa394` set this rule; the 5 phrases that remain follow it.
4. **A test so the two cannot drift** (a small file in `app/tests/`): (i) load every `urgent` array; (ii) for each phrase, assert both `words.js` `rankTopics` (already run in Node by `test_topic_search.py`) and the Python matcher flag it, in its plain form and with caps and a curly apostrophe; (iii) assert that on a fixed list of "must not flag" sentences ("trouble breathing", "wound not responding to antibiotics", "heat stroke on my tomato plants") neither side flags them as the choice; (iv) fail if any phrase of the Python-only tables duplicates a guide phrase. The same fixture file feeds both runtimes, so a change on one side shows up as a failing test.
5. **Order of work:** 1) agree the rule in point 3; 2) add the phrases for the 3 or 4 least contested choices (bleeding, allergy, poison, sudden); 3) Python reads them; 4) fork keeps its extras. Phrases like "heat stroke" or "heart attack" also hit information searches ("what is a seizure"): a maintainer should decide whether that is acceptable (guide first is arguably right).

## 6. What was not checked

- Whether the proposed phrases reorder real guide searches the way a reviewer wants: I measured text flags, not `rankTopics` ordering, and did not run guide search on the lists. Several topics may each name an urgent phrase for one search (up to 3 listed).
- Any language other than English; `words.js` handles all scripts, the fork's lists and the test lists are English (one French line is in the data).
- The category counts for `confidence.URGENT` come from a keyword heuristic in `measure.py`; kinds (plain/stem/optional/window) are likewise a regex-shape heuristic. Totals per source are exact alternatives counts; the split by category is approximate.
- The meaning check (`meaning_red`) was not run, as asked; its additions are not in (c) or (d).
- The held-out lists were written for the fork's own work; (c) was tuned against nearby wording, so its high numbers are not an out-of-sample claim.
- The triage set mixes clean and typo versions of the same question (362 rows from 159 topics' phrasings), so it is not independent either.
- Whether upstream will accept phrases for non-`hurt` topics (disaster, power, shelter, health): the field is documented for "life-threatening choices" and I mapped broadly; a maintainer may want only `hurt`.
