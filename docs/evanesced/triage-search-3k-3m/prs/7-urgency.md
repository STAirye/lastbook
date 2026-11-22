Urgency on one source: guide phrases, a meaning check, no encyclopedias on urgent questions, and an injury guard (triage search, part 7 of 8)

## What changes

The chat has to know when a question may be an emergency. Until now this was one list of words in `engine/confidence.py`
(part 5). This puts the phrases in the guides, where #167 already keeps them, lets a small meaning model add what the words
miss, and uses the label for two things: leaving the encyclopedias out of an urgent question's first results, and keeping
everyday how-to phrases from taking over a question about an injury.

**1. One source for phrases.**

- `content/topics/*.json`: `urgent` phrases for 11 guide choices (87 phrases; #167 had 8, on one choice). They are the
  phrases of an urgent-phrase mapping I measured on the author's fork that name a person's state or the event ("heavy bleeding", "snake bit", "throat
  closing", "took too many pills", "carbon monoxide poisoning"), never a bare word with a harmless sense (the rule upstream's
  commit e2fa394 set when it took "choking" and "unresponsive" out). Left out on purpose: "collapsed" and a bare "is choking" (also
  a tent, smoke); "cpr" (a proper phrase, but it changes how the search "cpr" alone ranks, which `test_english_ranks_as_before`
  pins: a maintainer's call); "chest pain" and "someone/baby is choking" (their words are in the labor guide's `context` entries,
  and `test_context_never_holds_a_life_threat` stops them); all of `health/pregnant` (the labor guide has its own
  phrases, `context` and `unless` words, with tests), and the disaster choices (their words, "house", "coming", "kitchen", clash with
  the same test). `content/SCHEMA.md` says what a phrase should be.
- New `engine/urgent_phrases.py` reads those fields in Python with the guide search's own word rule (lower case, NFKD, accent
  marks on Latin letters removed, split at anything that is not a letter, mark or digit, so "isn't" is "isn" and "t"; whole
  words in order, stop words counted).
- `confidence.urgent()` (part 5) now also takes a guide phrase as urgent. It keeps what a phrase cannot say, as a residual list in
  the same file: the wide stems (`URGENT`: `breath*`, `chok*`, `bleed*`, everyday wordings), the idioms to cut first (`NOT_URGENT`),
  the body signs and the typo handling. Idioms are cut before phrases too ("drowning in homework"). The texts passed are the question
  as typed and as typo-corrected, so "he isnt braething" names "isn't breathing".
- `app/tests/test_urgent_phrases.py` (13 tests) keeps the two sides from drifting: the Python word rule against `web/words.js` on
  the same strings (in Node), every phrase named by Python in plain, capitals and curly-apostrophe form, the guide search choosing
  the same choice, and sentences that only look like a phrase ("trouble breathing", "not responding to antibiotics") named by neither.

**2. `assistant.is_danger`** is true for a danger button, or for `confidence.urgent` (a guide phrase, the wide words, a body sign), or
else when the meaning check says so. `question_hits` uses it for `info['danger']`, where part 5 had left `confidence.urgent` alone.
The meaning check only adds: what the words call urgent stays urgent, and it never withholds a page.

**3. The meaning check** (`engine/meaning_red.py`). The question (typo-corrected, no prefix) is turned into a vector by bge-small
through part 6's `lastbook-llm --embed` process and compared with 31 averaged vectors from 689 invented example sentences (20 red
categories, 11 not red); `score = best red cosine - best not-red cosine`, urgent above 0.00837.

- Started from `server.init` on a thread of its own, once. It reads `ready.embed` from part 6's runner. Until it is ready, and
  whenever anything fails (a file missing or changed, no runner, a runner without `--embed`, one that ends or stops answering),
  the words alone decide; the log says so once. A runner that ended is started again up to 3 times. `LASTBOOK_MEANING_RED=0` turns it
  off. The desktop process loads no model and no onnxruntime; the runner is a second process that talks through its standard input
  and output.
- Its two files (a 37 MB q8_0 GGUF of bge-small-en-v1.5, MIT, and `centroids.npz`, 51 KB) are **not in the app**. Setup downloads
  them from Hugging Face (`STAirye/lastbook-meaning-red`, revision 591b1b97e8648a270bc82f1f2d2e335e401bda7d, pinned with size and SHA-256 in
  `engine/data/meaning_red_manifest.json` and checked before use) right after the person's own download of the local AI model
  (`Setup._meaning_red` in `engine/setup/api.py`; a failure leaves the model's install alone). A source tree can hold them in
  `derived/models/meaning-red/`. The downloader's host rules are unchanged (huggingface.co was already allowed).
- `engine/data/meaning_red_examples.jsonl` (the 689 sentences) and `tools/meaning_red_model.py` (builds both files from the
  Hugging Face model with llama.cpp's own converter, with fixed zip times so the same inputs give the same bytes) are here so the
  centroids can be checked and rebuilt. They are not needed at run time.
- `THIRD_PARTY_NOTICES.md` and `engine/data/meaning_red_LICENSE.txt` say where the model comes from.

**4. No encyclopedias for an urgent question** (the skip part 4 left out). `assistant.chat` labels the question first. If it is
urgent, `first_wiki` is not run, so the manuals have the first results to themselves ("prefer a manual for safety-critical steps").
The message then carries a `wiki_offer` event, and `web/chat.js` shows **"Not an emergency? Add the encyclopedias"**, which asks the
same question again with `wiki: true`. The chat's sidebar has a setting, **"Encyclopedias on urgent questions too"**, off by default
(`sg.wikiUrgent` in the browser; when on, every question is sent with `wiki: true`). `LASTBOOK_WIKI_URGENT=1` keeps the articles
server-side for every client. The label is the wide one, so it also skips the articles for some everyday questions ("how to use a
fire extinguisher"); that is why the button is there.
  *What I did about the thread:* the author's fork searches the encyclopedias on a thread beside the library search, to save about
  370 ms, and has to drop the result afterwards when the label turns out urgent. Here the label is computed first (about 10 ms with
  the meaning check), so nothing needs a thread, and `first_wiki` stays the synchronous call part 4 has. `web/index.html`
  (`chat.js?v=18`) and `web/sw.js` (`sg-shell-v16`) bumped.
  *The default differs from the fork's.* On the fork the setting is on by default, because there a vector index of the
  encyclopedias makes their articles good enough for urgent questions. That index is not part of this series, and with the keyword
  picker the articles for an urgent question are often weak ("he is not breathing": "Philips Breath Counter", "Conscious breathing"),
  so here the default is the manuals alone.

**5. The injury guard on everyday phrases** (left out of part 5, as it is a change to `server.py`'s topic search).

- `confidence.INJURY` and `confidence.injury(text)`: the injury words of `URGENT`, plus lungs, monoxide, inhaled, blisters,
  electrocuted, coughing. They are not `URGENT` itself, because its fire, smoke, gas, flood, baby and cut would also stop
  "how do i light a campfire".
- `server.PHRASES` takes an optional third item (a regex that, when found, switches the phrase off) and a fourth (`HOWTO`).
  A `HOWTO` phrase is not used when the question names an injury. `LASTBOOK_PHRASE_INJURY=0` turns the guard off.
- The phrases it guards are in this pull request too, since `main` has none: "start/make/light a fire" (tinder, kindling, firecraft),
  "make the water safe" (disinfect, purify, chlorine), and "water damage" (mold, flooding; not a how-to phrase, so not guarded).
  They are the ones from #128 (closed); **they can be dropped from this pull request without touching the rest** (the guard
  then guards nothing, and `HowToPhrases` in `test_bridge.py` goes with them). The exceptions #128's review asked for are there
  (no phrase for a fire in a kitchen or a building, or one being prevented or escaped; none for water intoxication, poisoning, lungs).
- The fork's retry without a phrase's helper words (`LASTBOOK_PHRASE_RETRY`) lost more than it won and is off there; it is not here.

`docs/TRIAGE-SEARCH.md` says what is in this pull request in sections 2, 4, 6, 7 and 8.

## Why

Issue #154 asked for search that treats a question as triage: an urgent question must get a useful first page, and a frightened
person must never be left with nothing. Proposal: #{ISSUE}. The maintainers asked on #154 to build on #167's `urgent` field so the
guide search and the document search don't drift, and this does: the phrases are written once, in the guides, and both sides read
them (point 1). Two things the words cannot do alone:

- **Words miss wordings.** "his throat is closing after peanuts" and "my son says voices are telling him to jump" have none of the
  wide words. A model that compares meaning catches some of those. It is used as a screen, like a triage rule that accepts false
  alarms: the label only means "never hold the pages back, show the buttons", so a false flag costs a few buttons. A miss costs more.
- **A label that is known first can do other things.** The encyclopedias are community-written background; for "he is not breathing"
  the manuals should lead, and the label is what says so (point 4). The same injury words keep "treat water in the lungs after
  drowning" from being read as "treat water" (point 5).

**This clashes with #168, #317 and #227 in one way.** They add meaning-based search (a bge-small index through the runner, or
sqlite-vec) and rank pages by it. This runs a meaning model by default, on every question, as part of the chat; but only to screen the
question for urgency, never to rank pages (ranking stays as the app has it). It would run next to any of them, and could share their
embedder if one lands first (part 6 explains the runner side). I would rather settle which goes first with their authors and the
maintainers than race.

## How it was tested

**Urgency is a screen, so it is held to a sensitivity target.** The reference is trauma field triage: the American College of
Surgeons Committee on Trauma aims for under 5% undertriage and accepts 25-35% overtriage [1]. Undertriage here is red lines not
flagged urgent, overtriage green lines flagged. High sensitivity first; overtriage is accepted because a false flag only adds
buttons and withholds nothing. The numbers below are from the author's fork unless they say they were run on this branch.

[1] American College of Surgeons Committee on Trauma, *Resources for Optimal Care of the Injured Patient* (2014), chapter 3, p. 28.
https://www.rumcsi.org/wp-content/uploads/2020/09/Resources-for-Optimal-Care-2014-v11-1.pdf

- **The phrases in the guides, on this branch** (the three independent lists and the triage set, 2,189 lines: 1,009 red, 367 yellow,
  813 green; `confidence.urgent` as the chat calls it, as typed and typo-corrected). #167's 8 phrases flag red 59 (5.8%), yellow 0,
  green 8 (1.0%). These 87: red 191 (18.9%), yellow 7 (1.9%), green 42 (5.2%). The wide words and body signs alone: red 961 (95.2%),
  yellow 297 (80.9%), green 395 (48.6%). All of them together: red 962 (95.3%), yellow 297, green 395. So **phrases do the narrow job
  (a choice that must come first in a guide search), not the wide one**: in the chat's screening they add a single red line to the
  wide words ("his throat is closing after peanuts"), and the wide words stay as the residual list for that reason. Where #167's
  field cannot say it, the words say it. The assistant's narrow `DANGER` list (used by part 8's routes) flags 258 of these lines, and
  every one is also urgent by the rules above, so `is_danger` here does without it.
- **The meaning check** (measured on the author's fork; words = the wide words with typo correction; red / yellow / green lines
  flagged; the examples were written before any list was opened, so lists 1-3 are out of sample for it):

  | | list 1 (343/104/243) | list 2 (249/111/246) | list 3 (199/78/254) |
  |---|---|---|---|
  | words only | 340 / 98 / 76 | 230 / 85 / 127 | 173 / 55 / 154 |
  | meaning only | 297 / 56 / 60 | 210 / 53 / 62 | 162 / 35 / 75 |
  | words OR meaning (shipped) | 341 / 100 / 104 | 243 / 93 / 147 | 188 / 62 / 173 |
  | red missed (undertriage) | 0.6% | 2.4% | 5.5% |
  | green flagged (overtriage) | 42.8% | 59.8% | 68.1% |

  Red caught only by meaning: 1, 13 and 15 lines; no line the words flag stops being flagged. The words alone miss 6-13% of the red
  lines of lists 2 and 3 (the first version missed 15% of list 1); the meaning check alone misses 13-19%, which is why it only adds.
  The green lines were written as look-alikes and mild symptoms, not as a sample of everyday questions, so the overtriage is an upper
  bound on that kind of text. Time through the pipe: median 5.2 ms, p95 8.9 ms (a busier run: 9 and 13 ms); the runner holds 66 MB
  and loads in 0.2 s.
- **List 4**, written by another model (Qwen3.5-9B, run locally; 832 messages, 525 of them Chilean and Mexican Spanish, mostly
  idioms; narrow): English red 58 of 65 (89%) as typed (words alone 54; 6 of the 7 misses are one doubtful template). Spanish red
  12 of 45 (27%) as typed, 43 of 45 (96%) with the English search words the chat's local AI writes for them. **The English search
  words are not part of these pull requests**, so on this branch a Spanish emergency is recognised about a quarter of the time.
- **The encyclopedia skip** (measured on the author's fork): all 131 red test questions skip the articles; so do 48 of 58
  yellow and 38 of 64 green ones (hence the button). The more precise label (danger signs or meaning only) would skip 9 green
  questions but miss 14 red ones, including "splashed bleach in my eye".
- **The injury guard, run on this branch** with PR 1's scorer (`score.py --mode keyword --sets issue154,issue128,triage`, a library
  pack copy, long pages in sections). Against the previous part's tip: #154's own useful count 145 -> **171 of 256** (typo versions
  150 -> 172); #128's 27 questions' mean useful pages 4.37 -> 5.30; the triage set's first page right 150 -> 153 and a useful page in
  the top 3 202 -> 204 of 253. The guard alone (the same code with `LASTBOOK_PHRASE_INJURY=0`): #154's count 153 -> 171 (typos 161 -> 172),
  its 13 red questions with a useful page in the top 3 9 -> 12, the triage set's 200 -> 204. So the how-to phrases alone help
  (145 -> 153) and the guard keeps them from hurting an injury question. The author's earlier fork numbers (144 -> 168) were on a
  different build.
- **Guide search**, run on this branch: `test_topic_search` and `test_topic_search_emergency` (Node, `web/words.js`) pass. #154's
  emergency fixture closes two of its recorded gaps: "treat water in the lungs after drowning" now opens the not-breathing choice
  (it opened "keep water clean") and "my clothes caught fire while starting the fire" opens the burn choice (it opened the
  earthquake guide); `BASE_FIRST` and `KNOWN_GAPS` in that file say so, as the file asks.

Tests:

- New `app/tests/test_urgent_phrases.py` (13): above.
- New `app/tests/test_meaning_red.py` (32, ported from the fork; 29 + 3): the manifest and the 689 examples; a stand-in runner for
  every failure (a runner that ends is started again 3 times, one that hangs, an old one, files missing or changed, the switch,
  six threads at once, stop); "words OR meaning" never takes a flag away; the process opens no listening socket, loads no model,
  leaves no runner behind. New: the server starts it, setup's fetch step (and that a pause still stops it while a failure does not),
  and the manifest's pinned repository and revision. 8 of them need the real files and runner and are skipped without them.
- `test_confidence.py` (34 -> 41): `is_danger`, a guide phrase, the injury words, and the chat leaving the encyclopedias out of an
  urgent question, offering them, and giving them back for `wiki=True` and `LASTBOOK_WIKI_URGENT=1`.
- `test_bridge.py` (+5, `HowToPhrases`): the three phrases, their exceptions (#128's reviewer's pairs), the guard and its switch.
- `test_chat_steps.py` (+1, Node): the offer button shows under the last message only.
- `test_what_ships.py` (+1): the builds ship the code, the manifest and the licence, and no `.gguf`.
- `test_topic_search_emergency.py`: the two baseline rows above. `test_bridge.py` sets `LASTBOOK_MEANING_RED=0` before `server.init`.
- Run one file at a time on Windows with `PYTHONUTF8=0`: `test_meaning_red`, `test_confidence`, `test_typos`, `test_wiki_pick`,
  `test_encyclopedias`, `test_encyclopedias_real` (skipped without the files), `test_wiki_routes`, `test_chat_steps`, `test_chat_tables`,
  `test_long_pages`, `test_bridge`, `test_retrieval`, `test_i18n_catalogs`, `test_what_ships`, `test_topic_search`,
  `test_topic_search_emergency`, `test_validate_topics`, `test_urgent_phrases`, `test_llm_local` and every other `test_*.py`: all pass.
  `test_setup` has the same 3 failures before and after (two map-space tests and the first-run job, as in the earlier parts).
  `test_battery` and `test_run_source_linux` only pass on Linux (fail or skip on Windows before and after this change).
  The meaning check's real-runner tests ran against the author's own Windows build of the runner (the same code as part 6, built on
  the fork) with the published files.
- Not run: the page in a browser with a real model; a Mac or Linux build of the packages (the Linux copy list, the macOS spec and
  the scans were edited and `test_what_ships` reads them, but no package was built).

## What it doesn't do

- **No conversation routes.** `assistant.turn_hits` (noise, correction, a new danger, a follow-up), `plea` (a bare "911" or "help")
  and the narrow `DANGER` list come in part 8. Here a later message of a chat is searched alone, as in part 5, and its label is
  `is_danger` of that message only.
- **The meaning model is not in the app.** No package bundles the GGUF; a package whose person never runs setup's model download has
  the words only. The fork's build scripts that bundle the files when they are present (`packaging/meaning_red_files.py`) are left out,
  since they also loosen the package scans' rule about model files.
- **No translation.** The model and the examples are English. A question in another language is checked as typed; the English search
  words that make the Spanish figure above work are a later step of this series.
- **No phrases for the choices whose words clash with the labor guide's tests, nor for ones with no choice yet** (drowning alone,
  electric shock, being trapped or crushed). They need guide content first, or a maintainer's call on the test.
- **A phrase does not bring a guide in.** `rankTopics` scores by words, and a phrase only picks the choice for a guide it already
  found: "kill myself" does not open the mind guide by itself. So most of the new phrases change nothing in the guide search; they
  are read by the chat's check, where a guide phrase is also covered by the wide words in all but one of 2,189 lines. They are there
  so that one list is the place to read and fix, and for guide search wherever the words also match.
- **No vector index of the encyclopedias, no retry without a phrase's helper words**, no `wiki_vectors.py`.
- The constants (the threshold, the 31 centroids, 689 examples) were set on the examples and checked on three lists written by one
  model family and a fourth by another; real people, especially non-native speakers, may score lower. The example sentences came from
  one model family too.

Part 7 of 8 of the triage-based search engine (proposal: #{ISSUE}); builds on #{PR6}. Until that one is merged, GitHub shows its changes here too; this part's own changes alone: [triage/6-runner-embed...triage/7-urgency](https://github.com/STAirye/lastbook/compare/triage/6-runner-embed...triage/7-urgency).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
