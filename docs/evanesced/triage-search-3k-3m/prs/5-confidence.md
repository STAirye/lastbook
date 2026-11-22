Tell when the search is probably wrong: confidence, buttons, never withheld pages, body signs (triage search, part 5 of 8)

## What changes

Chat answers from the first pages the search finds, whether or not they fit the question. This estimates, from the
search itself and without a model, how likely the first page is right. When it is probably wrong, Chat says so and
offers buttons. Pages are never held back.

- New `engine/confidence.py`.
  - **The estimate.** `estimate(hits, trace)` is a logistic model over cheap signals of one search: how many of the
    question's words (or synonyms) the first page and its title carry, the first keyword row's bm25 against how rare the
    words are, how many pages had every word, whether the first page is from a first-aid or emergency book (by title),
    and with meaning-based search the best cosine, how fast the cosines fall, how far the two searches agree and how
    many different documents the top 8 come from. The coefficients are plain numbers in `MODELS`, one set for
    keyword-only search (what the desktop app ships) and one for hybrid. How it was fitted and cut is in
    `docs/TRIAGE-SEARCH.md`, section 5.
  - **Three levels.** Below 0.60 it is `buttons`, below 0.25 it is `unsure`, else `sure`. An everyday question (one that
    may not be urgent) gets buttons only below 0.30, and `everyday_level` keeps the request to say more from ever sitting
    above those buttons.
  - **Words the library does not have.** `unknown_words(q)`: after typo correction and splitting, no content word at all,
    or most content words on fewer than 3 pages (keyboard mash, a glued question that could not be split). The fitted
    model has no signal for this, and a search for "jdjdk" can look fine, so the estimate is capped under both cuts. A
    question in another language, and words with digits ("EU2200i"), are left to the model.
  - **Urgent words.** `urgent(*texts)` is true when a text has one of a wide list of emergency words (`URGENT`), or a body
    sign. `NOT_URGENT` cuts everyday phrases out first ("bleed the brakes", "blood orange", "a breath of fresh air",
    "CPR certification"), and only the phrase goes: "bad breath and now he can't breathe" is still urgent. The list is
    wide on purpose: a match only means the pages are never held back, so a false match costs nothing.
  - **Body signs.** `body_signs(*texts)`: pulse, breathing, blue lips or skin, unconscious, choking, bleeding, seizure,
    chest pain, not moving, cold and clammy. A body word counts when typed right, or one plausible slip away (two for
    long words, first letter kept) and only if the library has the word on fewer than 50 pages: "puls" is pulse, while
    "pulses", "bloom", "breeding" and "chose" are words of their own, and "chore" is not choke. In a glued run the
    library does not hold ("mybbyisntbreathing"), a short list of stems is looked for. `LASTBOOK_BODY_SIGNS=0` turns
    them off.
- `engine/typos.py`: the body-fix part that PR 3 left out. `typos.body_fix` puts a body word one slip away right where
  `fix_word` leaves it because the library has the slip as a word ("puls" on 24 pages → pulse), and turns a glued run
  around a body word that could not be split into the stem's words ("mybbyisntbreathing" → "not breathing"), so the
  search finds the resuscitation pages instead of nothing. `LASTBOOK_BODY_FIX=0` turns it off. It imports
  `engine.confidence` inside the function, because confidence imports typos.
- `assistant.py`:
  - `_fts` and `hybrid` take an optional `trace` dict and fill it with what confidence reads: the word groups, how many
    rows had every word, whether the any-word fallback ran, bm25 per row, the cosines. Without it nothing changes.
  - `question_hits(q)` is the chat's first search plus `info`: the estimate, whether the question may be urgent, and the
    body signs it names.
  - `chat_level` / `chat_reply` decide what Chat does: answer; answer with buttons; or, when the search is very unsure on
    the first question of a chat, ask the person to say more. That reply always comes with the pages found, as sources
    the person can open (`UNSURE_PAGES`; `UNSURE_DANGER` for a question that may be urgent; only a search that found
    nothing says so, `UNSURE_TEXT`, `UNSURE_DANGER_NONE`). A question that names a body sign, or may be urgent and uses
    words the library knows, is never only asked: it is answered from its pages with the buttons.
    `LASTBOOK_CONF_URGENT_ANSWER=0` gives such a question the pages only.
  - A later message in a chat gets the buttons and the answer, never the request to say more: it is often a follow-up
    ("and at night?") that only means something with the earlier ones.
  - `chat` emits a `suggest` event (the buttons: Not breathing, Heavy bleeding, Burn, Poison, Fire, Something else;
    `style: 'compact'` for an everyday question) before the answer, and for the request to say more a `done` with
    `unsure: true`, the pages as its sources and no model call.
- `server.py`: `/api/retrieve` adds `confidence` (`{p, mode, level}`, or null with `LASTBOOK_CONF=0`). The page does not
  use it yet.
- `web/chat.js`: the buttons under the answer (full size, or smaller chips for an everyday question; the emergency
  choices red, "Something else" green; a click sends the label as the next message). A "please say more" reply is not an
  answer: no "linked to a page" legend, no "unverified" notice, and its pages are headed "Pages the library found".
  Chat's labels are plain English in `chat.js` on `main`, so these are too. `web/app.css` has the button colours and the
  compact size, scoped to `.suggest`. `web/index.html` (`chat.js?v=17`) and `web/sw.js` (`sg-shell-v15`) bumped.
- `engine/confidence.py` added to the Linux build's copied files and the macOS spec's hidden imports (the Windows build
  finds it through `assistant`).
- `docs/TRIAGE-SEARCH.md` sections 3, 4 and 5 say what is in this pull request and what comes later.

Switches: `LASTBOOK_CONF=0` (all of the estimate), `LASTBOOK_CONF_BUTTONS`, `LASTBOOK_CONF_UNSURE`,
`LASTBOOK_CONF_BUTTONS_EVERYDAY` (the cuts, 0 to 1), `LASTBOOK_CONF_UNKNOWN=0`, `LASTBOOK_CONF_URGENT_ANSWER=0`,
`LASTBOOK_BODY_SIGNS=0`, `LASTBOOK_BODY_FIX=0`.

## Why

Issue #154 asked for search that treats a question as triage: a frightened person must never be left with nothing, and
an urgent question must get a useful first page. Proposal: #{ISSUE}. Two things went wrong without this:

- Chat could not tell a good search from a bad one. A search for keyboard mash answers from whatever it found.
  "How to build a root cellar" answers from a winter survival handbook.
- A cautious reply can fail the person who most needs help. "He has no puls what do i do" got only "please say more":
  "puls" is on 24 pages of the library, so the typo corrector leaves it, and the urgent words had "pulse". A glued
  "mybbyisntbreathing" got no pages at all. So the rule is that pages are never withheld, and a question with a body
  sign is answered.

## How it was tested

The numbers below were measured on the author's fork, which has the same `engine/confidence.py` (the same coefficients,
cuts and patterns, compared programmatically; only comments and `INJURY` differ) on the 362 questions of the triage test
set (PR 1; 253 clean and 109 typo versions, 159 topics). The scorer from PR 1 does not measure the estimate, so I did not
rerun them on this branch. Nothing here depends on the meaning check or on conversations (PRs 7 and 8).

- **How well it tells.** Grouped cross-validation by topic (a topic's clean and typo versions in the same fold): AUC 0.78
  keyword-only, 0.74 hybrid, and calibrated: in each 25-point band the predicted and actual rates are within a few
  points. Inside conversations the same model ranks poorly (the first page is often one the earlier answer cited), which
  is why a later message only gets buttons.
- **How often it speaks.** Keyword-only, buttons on 43% of the test questions and the request to say more on 7%; 5 of 216
  right first pages got the request. Hybrid: buttons on 18%, the request under 1%. Buttons at 0.75 were tried first and
  fell on 68% of keyword-only questions (116 false alarms against 70 at 0.60).
- **Everyday questions.** Of the test set's 51 everyday questions, out of fold, keyword-only: 0.30 puts buttons on 2 (4%),
  none with a right first page ("how to build a root cellar", "tooth nocked out"); 0.35 would add two right first pages;
  the old 0.60 gave buttons to 16 (31%), 9 with a right first page. Hybrid never goes that low on an everyday question.
  51 questions is a small sample.
- **Words the library does not have.** Keyword-only "jdjdk" got p 0.38 and "qwertyuiop" 0.94. With the rule, all 7
  keyboard-mash questions of the glued set and 2 of its 3 unknown words get the request, keyword-only and hybrid, where
  all were answered before. It never fires on the 426 test questions.
- **Urgent words and body signs.** Danger signs alone caught 81 of the 218 red questions; the wide list catches 218 of
  218 (it was written together with that set, so this is in-sample). On a list of 690 lines written by someone who never
  saw the code (343 red), the first version found urgent 85% of red lines (99% after the changes below) and left 18 red lines with only "please say
  more" and no pages ("took 20 of her sleeping tablets", "he's out cold on the pavement") and 36 with pages and no
  answer; after the everyday wordings, the idioms and the rules above, 0 and 0 (hybrid 4 and 1 → 0 and 0). That list is no
  longer held out, since the wordings were written against it. Body signs: 107 of 599 questions across the triage sets
  name one; those that got only "please say more" went 2 → 0 keyword-only (1 → 0 hybrid) and those that got pages and no
  answer 9 → 0. "mybbyisntbreathing" now finds resuscitation pages first (0 → 8 useful of 8 keyword-only, 0 → 5 hybrid).
  No clean question's search words changed, and no question that showed pages shows fewer. Some of these lines also
  involve parts that are in later pull requests (the plea "911", the meaning check); I took only the figures the word
  rules alone explain.
- **Idioms.** Of the list's counterexamples (everyday sentences close to emergencies) 80% were urgent by the first
  version of the words and 17% now. Green questions flagged urgent 64% → 31%. A false match only means pages are shown.

Tests:

- New `app/tests/test_confidence.py` (34 tests, no library, no model: the library's words are given, `hybrid` is a
  stand-in that fills the trace, the model round is a stand-in). Signals are plain numbers and strong searches beat weak
  ones; the cuts and their environment overrides; the everyday cut; unknown words; the urgent words (including emergencies
  in everyday wording) and the idioms that are not; body signs (named, misspelled, glued, words of their own, the switch);
  what `_fts` leaves in the trace, on a small SQLite index; `question_hits`; and Chat's events: sure answers as before,
  buttons, smaller buttons for an everyday question, the request to say more without the model and with the pages, nothing
  found, an urgent or body-sign question answered from its pages, a later message only gets buttons, and the whole way
  from a stand-in `hybrid` to the events.
- `app/tests/test_typos.py`: `BodyWords` (4 new: "puls" → pulse, the glued run, words that stay, the switches) and the
  negation test now also checks the corrected text is urgent.
- `app/tests/test_chat_steps.py` (3 new, Node): the buttons are full size or compact and escaped, only under the last
  message, and a "please say more" reply has no legend or unverified-answer notice.
- `app/tests/test_bridge.py` (1 new): `/api/retrieve` returns `confidence`; null with `LASTBOOK_CONF=0`.
- `app/tests/test_what_ships.py`: `confidence` is in the Linux build and the macOS spec, and names no household place.
- Run one file at a time on Windows with `PYTHONUTF8=0`: `test_confidence`, `test_typos`, `test_wiki_pick`,
  `test_encyclopedias`, `test_encyclopedias_real` (skipped without the files), `test_wiki_routes`, `test_chat_steps`,
  `test_chat_tables`, `test_long_pages`, `test_bridge`, `test_retrieval`, `test_i18n_catalogs`, `test_what_ships`,
  `test_topic_search`, `test_topic_search_emergency`, `test_llm_local` and every other `test_*.py`: all pass. `test_setup`
  has the same 3 failures before and after (map space and the first-run job, as in PR 2 and 3). `test_battery` and
  `test_run_source_linux` only pass on Linux (fail or skip on Windows before and after this change).
- Not run: the page in a browser with a real model.

## What it doesn't do

- **No meaning check, no `assistant.is_danger`.** Whether a question may be urgent is decided by `confidence.urgent`
  alone here, with its own word list. PR 7 moves urgency to one shared source (the guides' `urgent` phrases,
  `assistant.is_danger` and the meaning check) and replaces this one.
- **No conversation routes.** A chat's later messages are not told apart (noise, correction, a new danger, a follow-up);
  they are searched alone as on `main`, and only get buttons. A first message that is only "ok" or "😭" has no letters
  to search, so it counts as unknown words and is asked to say more; "911" and "help" are not recognised as a bare plea
  yet. Both come with `assistant.turn_hits` in PR 8.
- **The question is not translated.** English search words for questions in another language are not part of this
  series' pull requests so far; such a question is estimated on the words as typed (`unknown_words` skips it).
- **No injury guard on how-to phrases.** The author's fork also stops a how-to phrase ("light a fire") from taking over a
  question that names an injury, using the injury words of the urgent list. That is a change to the topic search in
  `server.py`, a separate idea from this one, and comes with PR 7. `confidence.INJURY` is not here.
- **No encyclopedia skip for urgent questions** (PR 7).
- The constants (0.60, 0.25, 0.30, the 50-page body limit) were set on named failures and on the test set; the
  coefficients were not refitted after the unknown-words rule. The fitting script is on the author's fork.

Part 5 of 8 of the triage-based search engine (proposal: #{ISSUE}); builds on #{PR4}. Until that one is merged, GitHub shows its changes here too; this part's own changes alone: [triage/4-encyclopedias...triage/5-confidence](https://github.com/STAirye/lastbook/compare/triage/4-encyclopedias...triage/5-confidence).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
