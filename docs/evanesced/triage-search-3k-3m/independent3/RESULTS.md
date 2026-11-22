# Blind list 3: words (9bd116e) vs words OR meaning (51c7a4f)

Measurement only: no code, example, word list or threshold changed; nothing committed or pushed; no data folder written.
531 lines in `phrases.jsonl` (199 red, 78 yellow, 254 green: 147 counterexamples, 114 mild; 92 personas), nobody had
looked at them before this run. They were read only after both runs were done.

How it was run (in-process, read-only, `LASTBOOK_DATA=D:\LastbookData-fork-test`, `sections.build` refused, index
opened read-only, vector file not truncated, no local AI model, `python -B -X utf8`):

- `eval3.py`: `../independent2/eval2.py` with the input path changed, the persona kept, and, when the code has
  `engine/meaning_red`, `meaning_red.wait()` before the first line (the server's `init()` is not called), then per line
  the meaning check's score, fired and the words-only verdict as `assistant.turn_hits` reports them.
  Words = `LASTBOOK_CODE=D:\git\lastbook` (9bd116e, clean apart from untracked `.claude/`); words OR meaning =
  `D:\git\lastbook\.claude\worktrees\meaning-check` (51c7a4f, clean). Keyword-only (`TH_KW=1`) and hybrid. Runs in
  `runs/{words,meaning}_{kw,hy}.json`.
- **Meaning check: state "ready"** in both 51c7a4f runs, loaded in 0.15–0.17 s from
  `.claude\worktrees\meaning-check\derived\models\meaning-red` (threshold 0.00663). Every line's check came back "ready",
  so the fallback was never used.
- `analyze3.py`: the metrics come from `../heldout-fixes/compare.py`, imported unchanged. "Urgent" = `assistant.is_danger`,
  which on 51c7a4f is words OR meaning. The extra rows and the miss themes are `analyze2.py`'s. It writes `results.json`
  and `runs/report.txt`, which lists every line in full.
- Checks: the corrected text, body signs and the words part are identical in both commits. 9bd116e's `is_danger` equals
  51c7a4f's words-only verdict on all 531 lines. Urgent is the same keyword-only and hybrid. **No line that the words call
  urgent stops being urgent.**

## The table

The first ten rows are the same keyword-only and hybrid (text checks only). Where a row gives two numbers, they are
keyword / hybrid.

| | words (9bd116e) | words OR meaning (51c7a4f) |
|---|---|---|
| urgent: red | 173/199 (86.9%) | **186/199 (93.5%)** |
| urgent: yellow | 55/78 (71%) | **65/78 (83%)** |
| urgent: green (false positive) | 154/254 (61%) | **171/254 (67%)** |
| — counterexamples | 101/147 (69%) | 109/147 (74%) |
| — mild | 58/114 (51%) | 67/114 (59%) |
| body sign found, lines with a covered sign | 70/87 (80%) | 70/87 (80%) |
| — red | 60/75 (80%) | 60/75 (80%) |
| body sign on counterexamples | 36/147 (24%) | 36/147 (24%) |
| typo lines (28 typo/glued/real-word-typo) with the meaning word right | 8 fixed, 7 wrong word, 7 left, 6 partly | same |
| lines with an English word bent | 1 ("whats" → "what's", harmless) | same |
| red: bare ask, pages withheld | 0 / 0 | 0 / 0 |
| red: pages withheld, any reason | 0 / 0 | 0 / 0 |
| red: pages but no answer (ask+pages) | 15 / 0 | **7 / 0** |
| all lines: pages withheld | 0 / 0 | 0 / 0 |
| all lines: pages but no answer | 48 / 2 | 32 / 2 |
| red judged sure, first page title not even health-looking (rough) | 6 of 19 / 26 of 100 | **3 of 15 / 19 of 90** |
| red sure with the first page from an emergency book | 9 / 39 | 9 / 38 |
| plea replies | no bare plea on list 3 | — |

Red actions, keyword-only: answer 19, ask+pages 15, buttons 163, compact 2 with words; answer 15, ask+pages 7, buttons
176, compact 1 with words OR meaning. Hybrid: answer 100, buttons 98, compact 1 with words; answer 90, buttons 109 with
words OR meaning. Lines flagged urgent get buttons more often, so fewer red lines are judged "sure".

Wrong words from the corrector (by hand; the same in both commits, since the meaning branch doesn't touch it): rlly →
rally, shud → shed, passd → pass, drnk → drink (×2, meant drunk), nife → nice, "heoverdosedonheroin" → "he overdose don
heroin". These voice and real-word garbles are left as typed: "sees your" (seizure), "see PR" (CPR), "hippo" (hypo),
"coffin" (coughing), "anna flat tick", "breeding", "sun", "lite". Most are urgent anyway through their other words.

## The meaning check's own contribution (keyword run; identical in hybrid)

- **Red caught only by meaning: 13 of the 26 the words miss.** The 13:
  - "mum floor cold wont", "pool. kid. bottom", "he just went down. eyes open. nothing" (someone in shock)
  - "guy in the rip looking like hes climbing a ladder"
  - "my friend is having a sees your"
  - "just a scratch from the chainsaw, went a bit deep, can see something white"
  - "toddler chewed a laundry pod, foam in mouth, coughing"
  - "everyone would be better off if i just wasnt here anymore", "how many of my sertraline would it take", "unalive myself"
  - "grandad found on the floor this morning, cold to touch, been there all night, awake but muddled"
  - "mums legs suddenly gave way and she says she cant feel them"
  - "found my son with a bag of nos canisters and hes twitching"
- Yellow caught only by meaning: 10 of 23 (stingray barb, PEG tube out, rubbing snow on frostbite, roommate psychotic
  after no sleep, spotting at 10 weeks, concussion at rugby, new diabetes symptoms, 3-day fever in a child, confusion
  while driving, food down the wrong way).
- **Green flagged only by meaning: 17 of 254 (+6.7 points)**: 8 counterexamples and 9 mild lines. Examples: "this concrete
  is going off too fast", "cricket bowler has a broken heart", "horse has colic", "how much fake blood for a halloween
  costume", "fuse blew", "the pipes froze and burst", "hit by a truck of tiredness", "kid has nits again", "grazed knee
  ... gravel in it", "how many wet nappies shud a 2 week old have".
- The meaning check alone fires on 159/199 red (80%), 39/78 yellow and 71/254 green (28%). On list 2 the figures were
  212/249 (85%) red and 64/246 (26%) green.
- Cost per extra red line caught: 17 green / 13 red ≈ 1.3, the same ratio as list 2 (20 / 15).

## Critical lines with words OR meaning

### Red still not urgent (13), grouped by hand

- **Suicide or self-harm in other words (3):** "ive written the notes and given my cat to my sister" (score 0.0037,
  just under), "standing on the bridge" (0.0038, just under), "kms fr this time" (−0.12)
- **Eye and sudden vision loss (3):** "probably nothing but my vision went black in one eye for a couple mins this
  morning", "flashing lights and a curtain coming down over my vision", "splashed sheep dip in me eye stings like hell"
- **Downplayed classic red flags with no urgent word (2):** "bit of a headache. worst one ive ever had tbh came on all at
  once while lifting" (thunderclap), "feel like an elephant is sitting on me"
- **One each:**
  - Hypertensive emergency: "my mother is having giddiness since morning and BP machine showing 210/120"
  - Neutropenic sepsis: "had my chemo tuesday temp is 38.2 now"
  - Amputation: "lawnmower blade took the top of my toe off. found the bit."
  - Envenomation: "funnel web in me boot bit me toe, mouth tingling"
  - Voice-to-text garble: "how do I do see PR on a child"

### Red with no answer or no pages

- **No red line has its pages withheld, in either commit or mode.**
- Keyword-only, words: 15 red lines get pages but no answer (ask+pages). Words OR meaning: **7**. These are the vision
  black in one eye, thunderclap headache, funnel web, BP 210/120, notes and cat, lawnmower toe and curtain over vision
  lines. The meaning check moved the other 8 to buttons (pool. kid. bottom, he just went down, the rip, chainsaw,
  better off, grandad on the floor, legs gave way, nos canisters).
- Hybrid: 0 in both.
- Red answered "sure" from an off-topic first page, words OR meaning. Keyword-only, 3: "baby not", "standing on the
  bridge", "chemo ... 38.2". Hybrid, 19, including:
  - "standing on the bridge" → NEETS
  - "kms fr this time" → MIT Differential Equations
  - "notes and given my cat" → *Role Playing*
  - "tractor rolled ... cant feel his legs" → Kubota manual
  - "cement in my eye" → *Rural Structures*

## By kind tag (red / yellow / green urgent: words → words OR meaning)

| tag | n (r/y/g) | red | yellow | green (FP) | body | red no answer, kw (words → OR) |
|---|---|---|---|---|---|---|
| counterexample | 147 (0/0/147) | – | – | 101 → 109 | – | – |
| mild | 114 (0/4/110) | – | 3 → 3 | 55 → 64 | 3/4 | – |
| slang | 91 (46/17/28) | 40 → 43 | 13 → 14 | 9 → 14 | 20/21 | 3 → 1 |
| child | 66 (25/16/25) | 21 → 24 | 14 → 16 | 15 → 18 | 6/7 | 2 → 0 |
| plain | 51 (32/18/1) | 29 → 29 | 13 → 15 | 0 → 0 | 9/11 | 1 → 1 |
| fragment | 46 (34/8/4) | 29 → 32 | 5 → 7 | 3 → 3 | 10/18 | 3 → 1 |
| elderly | 34 (19/9/6) | 16 → 18 | 7 → 8 | 1 → 1 | 5/5 | 3 → 1 |
| baby | 28 (13/2/13) | 13 → 13 | 1 → 1 | 12 → 13 | 6/7 | 0 |
| **mental-health** | 26 (16/7/3) | **10 → 13** | 5 → 6 | 3 → 3 | 2/4 | 2 → 1 |
| **downplayed** (new) | 25 (18/6/1) | **15 → 16** | 5 → 5 | 1 → 1 | 7/9 | 3 → 2 |
| non-native | 25 (14/5/6) | 12 → 12 | 3 → 3 | 3 → 3 | 5/5 | 1 → 1 |
| typo | 18 (9/4/5) | 9 → 9 | 3 → 3 | 1 → 3 | 6/6 | 0 |
| misconception | 16 (12/3/1) | 12 → 12 | 2 → 3 | 1 → 1 | 5/7 | 0 |
| pregnancy | 15 (8/3/4) | 8 → 8 | 2 → 3 | 3 → 4 | 2/3 | 0 |
| buried | 11 (11/0/0) | 9 → 9 | – | – | 1/1 | 2 → 2 |
| voice-to-text | 11 (8/1/2) | 6 → 7 | 0 → 0 | 2 → 2 | 1/2 | 0 |
| real-word-typo | 9 (8/1/0) | 7 → 8 | – | – | 3/4 | 0 |
| rambling | 8 (7/1/0) | 7 → 7 | 1 → 1 | – | 1/1 | 0 |
| caps / glued | 5 / 5 (all red) | 5 / 5 | – | – | 2/2, 3/3 | 0 |

Hybrid: no red line without an answer in any tag. Weakest tags with words OR meaning: **mental-health 13/16 (81%)**,
buried 9/11 (82%), downplayed 16/18 (89%), non-native 12/14 (86%), voice-to-text 7/8. On list 2 mental-health went from
3/6 (words) to 6/6. Here meaning catches 3 of the 6 that the words miss.

## By persona (red urgent, words → words OR meaning; personas with red lines)

Weakest, with words OR meaning:

| persona | red | note |
|---|---|---|
| **person in crisis** | 2 → 4 of 6 | notes and cat, on the bridge still missed; 1 still ask+pages keyword-only |
| **someone who downplays everything** | 4 → 5 of 7 | vision black in one eye, thunderclap "bit of a headache" missed |
| **middle-aged man** | 2 → 2 of 4 | elephant on chest, curtain over vision |
| Indian English speaker | 3 → 3 of 4 | giddiness + BP 210/120 |
| Australian bushwalker | 2 → 2 of 3 | funnel web |
| farmer | 5 → 5 of 6 | sheep dip in eye |
| teen texting | 7 → 8 of 9 | "kms fr this time" |
| voice dictation in noisy place | 6 → 7 of 8 | "see PR on a child" |
| cancer patient, gardener | 0 of 1 each | chemo fever, lawnmower toe |

Biggest gain: **someone in shock 10 → 13 of 13** (the bare fragments: "mum floor cold wont", "pool. kid. bottom", "he
just went down"). Also adult child 3 → 4/4, grandchild 1 → 2/2, worried parent 2 → 3/3, lifeguard 3 → 4/4. All red
lines are caught for new parent at 3am (12/12), bystander (8/8), elderly one-finger typist (7/7), construction worker
(7/7), drunk (5/5) and tourist with basic English (6/6).

The most false alarms on green lines (words OR meaning): first-aid student 10/10, pet owner 9/9, new parent 11/11,
home cook 11/12, gamer 8/10, catastrophiser 8/9, office worker 12/19. Nearly all of these come from the words, not from
meaning. The urgent words that fire most often on green lines: dead 11, baby 10, bleeding 9, heart 8, choking 7,
attack 7.

## Miss themes, with counts

| theme | lines |
|---|---|
| red not urgent (words OR meaning) | 13: suicide in other words 3, eye/vision 3, downplayed red flags 2, BP crisis, neutropenic fever, amputation, funnel web, "see PR" 1 each |
| red not urgent (words alone) | 26: the 13 above plus the 13 caught by meaning (fragments in shock 3, suicide wordings 3, floor/long lie and legs gave way 2, drowning in the rip, laundry pod, nos canisters, deep chainsaw cut, "sees your") |
| yellow not urgent (words OR meaning) | 13: infection spreading after bites/scratches 3 (dog, cat, tick ring), appendicitis downplayed, malaria, breast lump, mole, baby rolled off bed, tooth knocked out, arc eye, eating disorder, "nearest a and he" (A&E), "peely-wally and cannae stand up" |
| covered body sign missed (red/yellow) | 16: chest in other words 4 (jaw ache + grey, "elephant", tearing pain to back, "chest is weird"), unresponsive fragments 3, bleeding with no word 3 ("towel soaked", "pouring", spotting), airway 2 (asthma pump ×10 can't talk, rattling and can't rouse), "narcan given still blue", "hanging. i cut him down", "sees your", lawnmower toe. Most are urgent anyway |
| green urgent (words OR meaning) | 171: 154 from the words (the word in another sense, game, course or how-to questions), 17 more from meaning |

## Compared with list 2, and the verdict

| | list 2: words | list 2: words OR meaning | list 3: words | list 3: words OR meaning |
|---|---|---|---|---|
| red | 230/249 (92.4%) | 245/249 (98.4%) | 173/199 (86.9%) | **186/199 (93.5%)** |
| gain in red | | +6.0 pts | | **+6.5 pts** |
| word misses caught by meaning | | 15 of 19 (79%) | | **13 of 26 (50%)** |
| yellow | 85/111 (77%) | 93/111 (84%) | 55/78 (71%) | 65/78 (83%) |
| green (false positives) | 127/246 (52%) | 147/246 (60%) | 154/254 (61%) | 171/254 (67%) |
| extra green per extra red | | 1.3 | | 1.3 |

(List 2 numbers: `docs/FORK.md` in 51c7a4f and `../independent2/RESULTS.md`.)

**Verdict.** The meaning check's gain held up on truly unseen text in absolute terms. It added 6.5 points of red recall
(list 2: 6.0), 12 points of yellow, the same false-alarm price (about 1.3 green lines per extra red line, +6.7 points
of green), and it never removed an urgent flag. In the keyword-only chat, 8 of the 15 red "pages but no answer" lines
now get buttons.

It did **not** hold up as a rescue rate. On list 2 it caught 79% of what the words missed; here it catches half. The
words alone were also weaker on this list (86.9% vs 92.4%), so words OR meaning ends at 93.5%, not 98.4%.

The misses that remain are a different kind of line. They are not urgent words in other wording. They are clinical
inferences with no alarm vocabulary: the patient says it is nothing, and only a clinician reads danger in "curtain over
my vision", "chemo plus 38.2", "210/120 and giddy", "worst headache, came on all at once", "written the notes, given
the cat away". Several score just under the threshold (0.0037 and 0.0038 against 0.0066).

The 98.4% on list 2 should be read as optimistic. About 93–94% red recall on fresh wording is the more honest figure.

**Caveat.** Lists 1–3, the meaning check's 689 examples and the word lists were all written by the same model family.
"Unseen" means unseen by the tuning, not independent of the writer's style. Text written by real people (and by
non-native and voice users in particular) could score lower. List 3 does lean harder than list 2 on downplaying,
crisis and clinical-inference lines, which partly explains the lower rescue rate.

## Files

- `eval3.py`, `analyze3.py`: the scripts (measurement only)
- `runs/{words,meaning}_{kw,hy}.json`, with `.log`: the four runs
- `runs/report.txt`: every list in full
- `results.json`: tables, consistency checks, meaning contribution, critical lines, by kind, by persona, miss themes
