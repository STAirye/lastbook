# Body signs and the fire/water phrase exceptions (2026-11-19)

Branch `fork/body-signs` from `fork/glued-words` 9712522, worktree `.claude/worktrees/body-signs`. Nothing pushed, no
servers, no data written. Numbers: `BODY_SIGNS.json` (made by `body_analyze.py` from `body/{before,after}_{kw,hy}.json`,
made by `body_eval.py`).

**How measured.** In-process and read-only as `conf_eval.py` / `run_sets.py` (sections build refused, read-only index
connections, vector file never truncated, no model), `LASTBOOK_DATA=D:\LastbookData-fork-test`, `python -B -X utf8`.
Before = 9712522 (worktree `glued-words`), after = this branch. Keyword-only (`TH_KW=1`, as the desktop app ships) and
hybrid. Per question the chat's first search (`assistant.turn_hits`, as a first message), scored with `score.py` against
the set's own P, and what the chat does with it (`assistant.chat_level` after; 9712522's same steps before): **answer**,
**buttons** (answer + buttons), **ask** (the bare "help me help you", no answer, pages only as consulted), **ask+pages**
(`UNSURE_DANGER`: pages, no answer). Conversations: the 52 of `convos.py`, last message, replies citing the previous
turn's top 3 PDF pages (as `turnhits_eval.py`). Glued set: 29 of 48 have a need (mash has none), scored on those.

## What changed

1. **Body signs** (`engine/confidence.py` `BODY_WORDS`, `BODY_PHRASES`, `BODY_GLUED`, `body_signs`): pulse/heartbeat,
   breathing, blue lips/skin, unconscious (unresponsive, collapsed, passed out, won't wake), choking, bleeding/blood,
   seizure (convulsions, a fit), chest pain, not moving (limp, floppy), cold and clammy/wet. Matched exactly, or one
   plausible slip away (two for words of 7+ letters), first letter kept, only on words the library has on fewer than 50
   pages; inside a glued run the library doesn't hold, a list of stems. A body sign: `urgent()` true, never noise, and
   `chat_level` turns "unsure" into "buttons" (the answer from the pages, with the buttons). `LASTBOOK_BODY_SIGNS=0`.
2. **Body words in the search** (`typos.body_fix`): a word fix_word leaves that is one plausible slip from a body word,
   on fewer than 50 pages ("puls" -> pulse); an unsplittable glued run with a body stem -> the stem's words
   ("mybbyisntbreathing" -> "not breathing"). `LASTBOOK_BODY_FIX=0`.
3. **Phrase exceptions** (`server.PHRASES`): fire-making not used with prevent/avoid/stop/risk/hazard/cause/escape/
   spread/safety/drill (not "bow drill"); water-safe not used with intoxication/poisoning/lungs/overdose.
4. `assistant.chat_level`: the chat's decision taken out of `chat()` unchanged, plus the body rule (so the eval uses it).

## Per set, before -> after

Columns: n (scored) | first right | top-3 right | useful (sum of 8) | no useful page | urgent (is_danger) |
answer / buttons / ask / ask+pages. One value = unchanged.

**Keyword-only**

| set | n | first | top 3 | useful | none useful | urgent | answer / buttons / ask / ask+pages |
|---|---|---|---|---|---|---|---|
| cases | 362 | 219 | 289 | 1743 -> 1747 | 57 | 311 | 198 -> 199 / 133 -> 138 / 1 / 30 -> 24 |
| cases154 (+typos) | 64 | 40 | 54 | 321 -> 325 | 4 | 56 | 28 -> 30 / 28 / 0 / 8 -> 6 |
| cases128 | 52 | 33 -> 35 | 44 -> 46 | 256 -> 258 | 5 | 26 -> 27 | 38 -> 37 / 9 -> 11 / 3 -> 2 / 2 |
| cases241 | 21 | 12 | 21 | 113 -> 115 | 0 | 16 | 12 -> 13 / 6 -> 5 / 0 / 3 |
| cases_glued | 48 (29) | 19 -> 20 | 25 -> 26 | 145 -> 153 | 4 -> 3 | 23 -> 24 | 27 -> 28 / 8 -> 9 / 11 -> 10 / 2 -> 1 |
| convos | 52 | 28 | 40 | 203 | 4 | 51 | 25 / 27 / 0 / 0 |
| **all** | 599 (580) | 351 -> 354 | 473 -> 476 | 2781 -> 2801 | 74 -> 73 | 483 -> 485 | 328 -> 332 / 211 -> 218 / 15 -> 13 / 45 -> 36 |

**Hybrid**

| set | n | first | top 3 | useful | none useful | urgent | answer / buttons / ask / ask+pages |
|---|---|---|---|---|---|---|---|
| cases | 362 | 275 -> 274 | 326 | 2077 | 13 | 311 | 298 / 64 / 0 / 0 |
| cases154 (+typos) | 64 | 45 -> 43 | 57 | 358 | 4 | 56 | 48 / 16 / 0 / 0 |
| cases128 | 52 | 43 -> 46 | 46 -> 49 | 313 -> 319 | 3 -> 0 | 26 -> 27 | 52 / 0 / 0 / 0 |
| cases241 | 21 | 17 -> 16 | 21 | 120 | 0 | 16 | 18 / 3 / 0 / 0 |
| cases_glued | 48 (29) | 22 -> 23 | 27 -> 28 | 161 -> 166 | 2 -> 1 | 23 -> 24 | 30 -> 31 / 6 / 11 -> 10 / 1 |
| convos | 52 | 33 | 42 | 253 | 1 | 51 | 44 / 8 / 0 / 0 |
| **all** | 599 (580) | 435 | 519 -> 523 | 3282 -> 3293 | 23 -> 19 | 483 -> 485 | 490 -> 491 / 97 / 11 -> 10 / 1 |

## Safety counts

| | keyword-only | hybrid |
|---|---|---|
| questions naming a body sign (after's detector) | 107 | 107 |
| ... bare "help me help you" before -> after | **2 -> 0** | **1 -> 0** |
| ... pages without an answer (ask+pages) before -> after | 9 -> 0 | 0 -> 0 |
| urgent pages lost (pages shown before, bare ask after) | **0** | **0** |
| urgent before, not after | 0 | 0 |
| urgent after, not before | 2 (both red) | 2 (both red) |
| red questions not urgent after | 0 | 0 |
| red questions with the bare ask after | 0 | 0 |

The bare asks before: "he has no puls what do i do" (cases128, keyword p 0.22) and "mybbyisntbreathing" (glued; both
modes, no pages at all). After: both urgent, both answered; "mybbyisntbreathing" is searched as "not breathing" and its
first page is right (resuscitation guidelines, 8 useful keyword-only, 5 hybrid). "he has no puls" is searched as "he has
no pulse": hybrid first right (0 -> 2 useful); keyword-only its first page is First Aid p.7 ("If there is no pulse, see
No Heartbeat"), the same as the clean "he has no pulse", which the CPR pattern scores 0 (the label gap of LESSONS_154).

The remaining asks: hybrid 10, all keyboard mash or unknown words of the glued set; keyword-only 13, the same 10 plus
"tooth nocked out" (yellow), "whats the best way to lite a campfire" and "no sope how do i wash my hands" (green). None
names a body sign or is red.

## Every question that changed

Keyword-only (19):

- Body rule, ask+pages -> answer with buttons (red, same pages): "my sun isnt brething", "deep cut on the arm bleeding a
  lot", "knife wound to the chest and he is struggling to breathe", "fell off the roof and can not move his legs", "fell
  of the roof cant move legs", "someone fell in the rainwater pool and isn't breathing" (cases, and cases154 with its
  typo), "hes chalking help" (glued autocorrect, labelled not red).
- "he has no puls what do i do": searched "...pulse...", not urgent -> urgent, ask -> answer, first page Fluid Power ->
  First Aid p.7.
- "mybbyisntbreathing": searched "not breathing", ask -> answer, first right 0 -> 1, useful 0 -> 8.
- "how do i prevent a generator from starting a fire" (+ typo): first right 0 -> 1 (USMC winter handbook -> Aviation
  Maintenance fire-prevention page), useful 2 -> 3.
- "make a fire escape plan for my family" (cases, cases154 clean + typo, cases241): Army ATP 3-50.21 -> "Make a Family
  Emergency Plan", useful 4 -> 8 / 6 / 6 / 6, buttons -> answer.
- "how do i treat water intoxication" (+ typo): still no right page (wastewater -> microbiology), answer at p 0.66 ->
  buttons at 0.28.

Hybrid (10):

- "he has no puls what do i do": first right 0 -> 1, useful 0 -> 2, urgent (it was already answered: p 0.65).
- "mybbyisntbreathing": first right 0 -> 1, useful 0 -> 5, ask -> answer.
- "how do i treat water intoxication" (+ typo): first right 0 -> 1, useful 0 -> 3 ("Food and Water in an Emergency").
- "how do i prevent a generator from starting a fire" (+ typo): Honda generator manual first now (scored as before),
  useful 8 -> 7.
- "make a fire escape plan for my family" ×4: first right 1 -> 0 ("Mult-Family Home escape routes" -> "Make A Plan", a
  family-plan page the ESCAPE pattern doesn't match; as LESSONS_154 found).

Nothing else moved: no clean question's searched words changed (the body fix only touched "puls" and the glued run), no
route changed, and the conversations are identical in both modes.

## Narrowing urgent(): measured, not changed

Keyword-only, all sets but the conversations: 83 of 171 green/counterexample questions are urgent. What dropping a word
from URGENT would cost (red or yellow questions that are urgent only through that word, with no danger sign or body
sign) against green ones relieved:

| word dropped | red/yellow that lose urgency | green relieved |
|---|---|---|
| fire | 15 (grease fire, fire in the house ...) | 28 |
| gas | 4 (i smell gas ...) | 0 |
| generator | 2 (dizzy after the generator inside) | 1 |
| baby | 5 (scald on the baby, baby is coming) | 5 |
| bleach | 3 (bleach in the eye, mysonatebleach) | 3 |
| car | 1 (water coming into the car) | 0 |
| dead, emergency | 0 | 1, 5 |

The body-sign list covers none of the everyday false matches (they are fire, gas, baby, bleach, generator ...), so it
cannot narrow urgent() safely. Only "dead" and "emergency" could go without a red loss on this set, and both are words a
real emergency uses ("he looks dead", "this is an emergency"); left as is. Narrowing needs the sense of the word (fire as
making, gas as fuel), i.e. #167's `urgent` phrases.

## Tests

Every `app/tests/test_*.py`, one process per file (`run_unit.sh`, `body/unit_after.txt`): all pass, nothing that passed
fails. New: `test_confidence.BodySigns` (3: named and misspelled signs, words of their own, switch),
`TurnHitsConfidence.test_body_signs` ("he has no puls", glued no-breathing, never noise, switch),
`ChatConfidence.test_very_unsure_with_a_body_sign_answers`; `test_typos.BodyWords` (4); `test_bridge.ForkSearchWords.
test_how_to_paired_with_its_safety_or_medical_counterpart` (10 pairs from #128 and #154). `test_no_how_to_phrase_in_an_
injury_question`'s switch check now skips "water in the lungs" (its own exception now). Counts: test_bridge 168 -> 169,
test_confidence 28 -> 33, test_typos 18 -> 22.

## Caveats

- The body list was written alongside these sets; 107 questions match it. Its slips were checked against the real
  library's words (pulses 560 pages, bloom 259, breeding 581, chose 359 stay; chore 16 and blond 11 are not plausible
  slips), but recall on new wording is unknown, and a few odd matches cost an answer instead of a request ("my tent is
  cold and wet", "bad breath", "the pulse of the city").
- The chat's events were checked by unit tests (stand-in model), not in the browser or with Gemma.
- #241's guide-search test is not on this branch (pre-1.1.12 base); nothing here touches `web/words.js`.
