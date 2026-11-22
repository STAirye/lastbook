Tell what a chat message is to the conversation, and search other languages in English (triage search, part 8 of 8)

## What changes

Chat searches the newest message on its own. That is fine for a first question. Inside a conversation it goes wrong in
three ways: "ok" or "😭" is searched as if it were a question; "no, I mean the smoke" brings back the pages the person just
rejected; and "THE KITCHEN IS ON FIRE" after a water question gets water pages. A question in Spanish finds nothing, because
the library and its keyword search are English. This part fixes those, for the local AI's chat. It has two separate sections:
**A** (the conversation) and **B** (English search words). B does not depend on A's routes, but both are part of the same first
search, so they are in one pull request.

### A. The conversation routes

- `assistant.turn_hits(messages, english, followup, k)` replaces part 5's `question_hits`. It labels the newest user message
  and searches without a model:

  | Route | When | What is searched |
  |---|---|---|
  | `first` | one message, or no earlier message that is not noise | its own search (same search, label and confidence as before) |
  | `noise` | a stock phrase ("ok", "sorry wrong chat", "wait"), no letters at all, or mostly not words ("jdjdk") | no new search: the last sensible message's results again, plus buttons. With nothing sensible before it: its own search, buttons, and a request for more words |
  | `correct` | starts with "no no", or has "I mean", "not that", "that's not", "wrong one", "instead" | correction words stripped; pages the person saw last time go to the end; none carried over |
  | `danger` | a danger sign none of the earlier messages had, or a danger button | its own best 5, then the joined search; none carried over |
  | `follow` | everything else | the pages the previous answer cited, its own best 4, the search joined with the earlier message, the rest |

  Noise never becomes "the earlier message". "Not words" is judged against the library's own words (every term on 20 or more
  pages), one slip away included, and as typo-corrected too, so a glued "heschuokinghelkp" is not noise. A message in another
  language, or one that names a body sign, never is.
- **`DANGER` and `danger_signs`** (15 narrow patterns: not breathing, choking, bleeding a lot, seizure, on fire, snake bit,
  swallowed bleach, ...). They tell a new emergency from the one the conversation is already about, and they now also join
  `is_danger`, which part 7 left without them. On the three lists and the triage set they flag 258 of 2,189 lines and every one is
  also urgent by part 7's rules, so no label there changes.
- **A bare plea** (`plea`, `PLEA_TEXT`): a first message that is only "911", "help", "hlep", "HELP ME", "sos", "emergency" (with
  "please", "me", "now"... around it). There is nothing to search, but someone may be in danger. The chat shows the emergency
  buttons first, full size (`style: 'urgent'`), asks what is happening, and still gives the pages the search found. It counts as danger.
- **`chat_level` / `chat_reply`** read the route. Noise keeps the earlier answer and adds buttons, with "Still about: <the last
  sensible question>" first. The request to say more is only for a first question or a new emergency (part 5 allowed it for the
  first question only); a correction or follow-up gets the buttons, because inside a conversation the first page is often one the
  earlier answer cited. Without the routes every message after the first is treated so, as in part 5.
- `suggest_choices(info)` adds the "Still about" button. `web/chat.js` draws it green (like "Something else"), draws a plea's
  buttons first and larger, and accepts the `urgent` style (`web/app.css`: `.suggest.urgent`).
- **Only for the local AI.** `chat` uses the routes when the local AI is on (`LASTBOOK_AI_FOLLOWUP=0` turns them off). With another
  model a message is searched alone, as before. A first message is the same either way.
- `cited_before` finds the pages the previous answer cited from what `chat.js` `history_()` already sends ("(Title, p. 12)"),
  so a follow-up has them again with this turn's keys. Nothing in `chat.js` changes for that.
- The encyclopedia search uses the words `turn_hits` searched with (a follow-up's joined words, or the English words below).

### B. English search words for another language

- `needs_english(q)`: does the question look like it is not English? Letters beyond a-z, or more Spanish, Portuguese or French
  function words than English ones. A word with an accent inside an English question is not enough ("jalapeño burns on my hand").
- `english_query(question, earlier, cancelled)`: the local model, already needed for the answer, writes the question as 2 to 5 English
  search words (one call, thinking off, at most 32 tokens, `REWRITE` as the prompt). The earlier question goes along, so "¿y de
  noche?" is read after the right question. Results are kept per question. For such a question the model is started before the
  search instead of after it.
- `english_words(text)`: the reply is used only if it is not itself non-English and **at least half its words are English words**
  (`typos.english_words()`, part 3's list). Without that check, "respirar humo incendio" passed as English, because it holds none of
  the Spanish function words, and a red question was searched in Spanish (found through list 4). If the first reply is not English
  the model is asked once more ("Write the words in English"); if that fails too, the question is searched as typed.
- `turn_hits(..., english)` searches with the English words first, and with the question as typed if they find nothing. The urgency
  label, body signs and encyclopedia search use them as well.
- The answer gets one note (`LANGUAGE_NOTE`: searched in English with these words, search again in English, answer in the question's
  language). `web/chat.js` also knows the three special headings in Spanish ("No encontrado en la biblioteca", "Las fuentes no
  coinciden", "Mi propio razonamiento"), only as headings, and starts a sentence after ¿, ¡ or a capital like É or Ñ for the
  uncited-sentence marks.
- English questions skip all of it. `LASTBOOK_AI_ENGLISH_SEARCH=0` turns it off. It needs the local AI.

`web/index.html` (`chat.js?v=19`, `app.css?v=29`) and `web/sw.js` (`sg-shell-v17`) bumped. `docs/TRIAGE-SEARCH.md` says in sections 4, 5
and 7 (and 7.1) what is in this pull request; its introduction now describes parts 1 to 8 of the series.

Switches: `LASTBOOK_AI_FOLLOWUP=0` (no routes), `LASTBOOK_AI_ENGLISH_SEARCH=0`.

## Why

Issue #154 asked for search that treats a question as triage: an urgent question must get a useful first page, and a frightened
person must never be left with nothing. Proposal: #{ISSUE}. In a conversation a frightened person writes "ok", "no, I mean the
smoke" or "911", and the pages that come back should be about what they mean now. And a person who writes in Spanish should not get
Spanish leaflets: on a list written by another model, the urgent check recognised 12 of 45 Spanish emergencies as typed and 43 of 45
with the English words (below).

## How it was tested

Run on this branch with PR 1's scorer (`score.py --sets conversations,triage`, a library pack copy, long pages in sections), the last
message alone (the tip of part 7) against `turn_hits` (this branch). The scorer sends an empty reply for each earlier answer, so
`cited_before` finds nothing here: it measures the routes and the joined search, not carried pages.

| 52 invented conversations | first result right | useful page in top 3 | every need covered | no useful page | mean useful of 8 |
|---|---|---|---|---|---|
| keyword-only, message alone → routes | 21 → 22 | 29 → 31 | 35 → 45 | 13 → 3 | 3.46 → 4.25 |
| hybrid, message alone → routes | 27 → **25** | 37 → 36 | 38 → 46 | 10 → 1 | 4.17 → 5.17 |

So the routes find a lot more of what the person needs, and do not by themselves put the right page first: in hybrid mode corrections
went 11 → 9 of 14 right first, while follow-ups, additions and new emergencies were level (6, 6 and 4). Groups are 14, 19, 14 and 5, so these
are small. The triage set's single questions are unchanged (first right 153, top 3 204 of 253, keyword-only).

Quoted from the author's fork, not rerun here:

- The fork's own comparison of the same 52 conversations scored the routes against an earlier follow-up search that always followed
  the message before (not against searching the message alone), with replies that cite pages: hybrid first-right overall 56% → 64%;
  corrections 29% → 57%, new emergencies 0% → 80%, follow-ups 86% → 86%, additions 68% → 47% (worse), messages after noise 75% → 58%.
  The classifier was written together with these conversations, so its accuracy there (noise 11 of 12, corrections 14 of 14, new
  emergencies 5 of 5) is optimistic.
- English words, 8 Spanish questions with the local Gemma 4 E4B (fire without matches, creek water, a tourniquet, ...): answers cited
  and on topic 8 of 8, against 5 of 8 searched as typed, at about 2 to 3 seconds more per question.
- List 4 (832 messages written by Qwen3.5-9B run locally; 525 in Chilean and Mexican Spanish, mostly idioms; narrow, and its labels are
  that model's): Spanish red lines recognised as urgent 12 of 45 (27%) as typed, 43 of 45 (96%) with the English words, and an emergency
  book in the top 3 for 2% / 4% (keyword / hybrid) as typed and 73% / 82% with them. The English words also carry idioms over ("estoy
  muerto después de bailar" → "dead"): Spanish counterexamples flagged 7% → 19%, which only means more buttons. The check that the
  words are mostly English came after that run and moved Spanish red from 43 to 44 of 45.
- Live, with Gemma 4 E4B on a desktop: a nonsense question inside an urgent conversation and a shelter question gave good cited answers.
  A correction message or a new emergency in the middle of a conversation has not been seen live.

Tests:

- New `app/tests/test_turn_hits.py` (42; no library, no model; `hybrid` is a stand-in with canned pages, the model round is a stand-in).
  Every route; noise never becoming the earlier message; a correction dropping the pages already shown; a new danger sign carrying
  nothing; one message searched as before; the plea; the levels inside a conversation; `cited_before` on the browser's "(Title, p. N)"
  and a title with parentheses; `needs_english` on questions in four languages, and English ones with an accent in them; what `english_words` accepts and refuses; the model being asked once, kept,
  asked again when the reply is not English, and failing; and `chat` end to end: noise keeps the answer and offers the last question,
  a plea gets the buttons first, a message is searched alone without the local AI or with the switch, the English words are
  searched, noted and passed to the encyclopedias.
- `app/tests/test_confidence.py` and `test_meaning_red.py`: `question_hits` became `turn_hits` (one message); the meaning check's
  result is in `info['meaning']`.
- `app/tests/test_chat_steps.py` (+5, Node): a plea's buttons come first; "Still about" is green; Spanish headings; Spanish sentences.
- Run one file at a time on Windows with `PYTHONUTF8=0`, every `test_*.py` of the repository. All pass except: `test_setup` has the
  same 3 failures before and after (two map-space tests and the first-run job, as in the earlier parts); `test_battery` fails on
  Windows and `test_run_source_linux` skips, before and after.
- Not run: the page in a browser; the English words and the routes with a real model on this branch.

## What it doesn't do

- **No conversation routes without the local AI.** With another model a later message is searched alone, as on `main`. The routes were
  built and measured around the local model's chat, and I would not change the other path without a reason.
- **English words only for Spanish, Portuguese and French, and anything with letters beyond a-z.** `needs_english` counts a short list
  of function words; German or Dutch in plain a-z letters is not recognised, and is searched as typed.
- **No translation of the answer's headings except Spanish**, and no other language's idioms. The model, the examples and the typo
  rules stay English.
- **The routes do not raise the first page right** against searching the message alone in hybrid mode (table above); the gain is in
  what is covered. A correction in hybrid mode did slightly worse on the scorer's empty replies.
- **No citation repair, no history rewriting, no own-model-file or thinking changes** (fork-only, in `llm_local.py` and `assistant.py`),
  and no vector index of the encyclopedias.
- The classifier is a set of patterns written with its test conversations, and it misses gibberish made of real words ("the duck is
  a mint").

Part 8 of 8 of the triage-based search engine (proposal: #{ISSUE}); builds on #{PR7}. Until that one is merged, GitHub shows its changes here too; this part's own changes alone: [triage/7-urgency...triage/8-conversation](https://github.com/STAirye/lastbook/compare/triage/7-urgency...triage/8-conversation).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
