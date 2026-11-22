# A triage-based search engine: what the fork changed, why, and how it was tested

This is a huge module for the search part of Lastbook. It has a total of about 3,800 lines of code, 6 sub-modules and
about 200 tests, and has relentlessly consumed my waking hours (and Claude's tokens) for the past week. All my PRs on
bugfixing have been nearly accidentally discovered while building this.

I really hope it helps people navigate hard times, as one of my personal beliefs is that you need to prepare for the
worst hoping it will never come to pass.


Draft for upstream (Immortal-Protocols/lastbook). Not posted. Supersedes `upstream-triage-summary.md`. Updated
2026-11-21: live tests done, the meaning-check model published, the urgency mapping onto #167 measured, overlapping
upstream work (#302, #168, #287) taken into account, a fourth blind list run, numbers checked against the code.

**Every formula, constant and measure, and how to rerun each number:** [upstream-search-methods.md](upstream-search-methods.md)
(its section 12 lists where earlier write-ups disagreed with the code, and what is not recorded).

## Why

Lastbook is used when someone is scared, in a hurry and offline. The person types fast, misspells, glues words together,
names the setting instead of the problem ("treat water in the lungs after drowning"), or writes a second message that
corrects the first ("NO NO I MEAN he's choking"). Library search was built for calm questions: whole-word keyword
matching over pages, the same ranking for "how do I light a campfire" and "my son isn't breathing".

So the search was treated as a **triage problem** (issue #154): each question has an urgency (red = life at risk now,
yellow = care soon, green = how-to), the most urgent need wins, the emergency page must not be buried under pages about
the setting, the top results must not all be one topic, and a frightened person must never be left with nothing.

The design takes its inspiration from medical triage, which is built around **sensitivity, not specificity**: missing
someone who is in danger (undertriage) costs far more than a false alarm (overtriage), so a triage system accepts many
false alarms to miss very few. Trauma field triage states this as targets: the American College of Surgeons Committee
on Trauma aims for under 5% undertriage, and "Most agree that an acceptable percentage of overtriage is in the range of
25 to 35 percent" [1]. The search's urgency label follows the same rule. The trade-off is even easier here: trauma
triage limits overtriage because every false alarm spends scarce, expensive hospital resources (a trauma team, a
transfer), while a false alarm in the search costs almost nothing (the pages are shown anyway, with emergency buttons,
and nothing is withheld), and the rules themselves are cheap to change and remeasure. So undertriage is held to their
target, and overtriage may run above their range. How the numbers compare is in "The meaning check" below ("Why it is
tuned for sensitivity").

Two layers, because the desktop app is keyword-only by design:

- **No model:** keyword search and word rules that work everywhere.
- **Meaning-based,** where a model is available: hybrid search (bge-small vectors) and a meaning check for urgency,
  run in the app's own llama.cpp runner, never in the desktop process.

## Problems found and what fixes each

| Problem | Fix | Effect (measured) |
|---|---|---|
| 351 saved web pages are whole books (up to 4.4 MB) and match nearly any question: *Modern Machine-Shop Practice* came up for 26 of 362 test questions | Long pages cut into ~5,000-character sections (7,623), in a fork-owned index file (the pack's `search.sqlite` is checksummed and untouched); the reader opens the section | Sections alone: 26 → 1 (hybrid), 25 → 6 (keyword-only); with the typo and conversation changes 26 → 4 |
| The same in the encyclopedias (1.1.13 adds 3 articles to Chat's first results): whole books stored as one article came first ("Mirad Grammar/print version" for "my toddler drank bleach"), and the useful words were past the first 2,000 characters in most articles | The same sections: each article scored by its best section, the excerpt taken from there; print versions and huge articles skipped. The library and the encyclopedias are searched side by side and shown apart, each in its own order | First article useful 36% → 58% (253 questions); a merge by score was tried and dropped (it put articles above useful manual pages) |
| Keyword search needs whole words: "breating" matches nothing, so the emergency drops out | Typo correction against the library's own words, weighted to emergency books; glued words split ("heschuokinghelkp" → "he's choking help"); contractions keep their negation ("hasnt" → "hasn't"); real English words never bent (a general English word list) | Useful pages for typo questions 2.23 → 4.72 of 8 (keyword-only); 0 clean questions changed; English words bent 35–46 → 0 on independent lists |
| A conversation's second message: corrections bring back the rejected pages, a new emergency gets the old topic's pages | The newest message is classified without a model: noise / correction / new danger sign / follow-up | Corrections first-right 29% → 57%, new emergencies 0% → 80% (hybrid; small groups: 14 and 5 conversations, before and after measured by different paths) |
| No way to tell a good search from a bad one | A tiny logistic model on signals search already has (word coverage of the first page, match strength for the words' rarity, emergency book or not; with vectors also cosine and agreement) | AUC 0.78 keyword-only, 0.74 hybrid, calibrated; buttons below 0.60, "help me help you" below 0.25, everyday questions only below 0.30 and with smaller buttons |
| The "help me help you" reply could leave someone with no pages at all ("took 20 of her sleeping tablets") | Pages are never withheld; urgent questions get an answer from the pages plus buttons; a bare "911" / "help" gets the emergency buttons | Red messages with no answer or no pages: 18 → 0 (independent list 1), 17 → 0 (list 2) |
| Urgent questions not recognised as urgent | Word rules for body signs, matched through typos ("he has no puls"), plus a meaning check (below) that can only add urgency | Red caught on a list nobody had seen: 86.9% words → 94.5% words + meaning |
| Everyday phrases ("how do I light a campfire") found fire-safety pages; the fork's fix then hijacked injury questions ("treat water in the lungs after drowning" → wastewater manuals) | Phrases skipped when the question names an injury or a safety purpose (prevent, escape, intoxication…) | Drowning 0 → 4 useful pages, #154's useful count 144 → 168 of 256 (keyword-only); how-to gains kept |

## The meaning check, and why it runs in the llama.cpp runner

Word lists caught 100% of red questions on our own test sets but **85% on the first independent list**. Adding words
helped about half as much on the next unseen list: the lists learn the wording they were built from. On lists they were
not built from, the words alone still catch **83–87%** (list 3: 87%; list 4's English lines: 83%). So urgency also gets
a meaning-based second opinion, which brings that to **89–94.5%** (list 3: 94.5%; list 4: 89%):

- The question is embedded with **bge-small-en-v1.5** (BAAI, MIT; 33M parameters, 384 numbers per text) and compared
  with 31 averaged vectors from ~690 invented example sentences (20 red categories, 11 non-red). If it is clearly closer
  to a red category, it counts as urgent. It **only adds** urgency, never removes it.
- It runs in a **second, CPU-only `lastbook-llm --embed` process** with a 37 MB q8_0 GGUF, using the `libllama` the app
  already ships (the runner gained an `--embed` mode, about 100 lines). The desktop process loads no model: upstream's
  `test_no_listening_socket_and_no_model` passes unchanged, and Mac/Linux builds get no new runtime.
- Ready 0.2 s after start, about 66 MB of RAM, 5.2 ms per question (median; 8.9 ms p95). Any failure (no runner, old runner, missing or
  changed file, dead process) falls back to the word rules.
- The two files are published at https://huggingface.co/STAirye/lastbook-meaning-red (commit 591b1b9), pinned with
  their SHA-256 in the app's manifest and checked before use; setup downloads them after the local AI model.
- An onnxruntime version was built first and gave the same results; it was dropped because it put a model and a runtime
  in the desktop process.

**Why it is tuned for sensitivity.** The urgency label works like a screening test, not a diagnosis: missing an urgent
question costs far more than a false alarm, and a false alarm is cheap (the pages are shown anyway, with emergency
buttons; nothing is withheld). The reference is trauma field triage: the American College of Surgeons Committee on
Trauma aims for under 5% undertriage and accepts 25–35% overtriage [1]. Undertriage here = red lines not flagged urgent; overtriage
= green lines flagged. On the three independent lists, words OR
meaning miss 0.6% / 2.4% / 5.5% of red messages; the meaning check alone misses 13–19%, which is why it only adds to
the words. It flags 43–68% of the green lines, but those were written as hard look-alikes and mild symptoms, not a
random sample of everyday questions.

## Urgency and #167's `urgent` field

Maintainers asked on #154 to build on #167's `urgent` field so the guide search and the document search don't drift.
The fork's rules were measured against it (2,189 lines: the three independent lists and the triage set):

| Flagged urgent | Red | Yellow | Green |
|---|---|---|---|
| #167 as merged (5 phrases, Not breathing) | 3% | 0% | 1% |
| 117 phrases in #167's format for every urgent guide choice, matched exactly as `words.js` does | 16% | 2% | 10% |
| The fork's word rules (with typo correction, without the meaning check) | 95% | 81% | 49% |

The field picks the right guide; it can't be a screening net, and most of the fork's rules can't be written in it
(phrases with words between them, typo slips, glued words, idioms to skip such as "drowning in emails"). So the
proposal is one shared source, not a second rule set:

- The `urgent` phrases in `content/topics/*.json` filled in for every urgent guide choice (small guides PRs, in the way
  upstream already takes guide-search fixes; upstream's own pruning of ambiguous phrases in e2fa394 kept).
- The library search reads those same phrases, and adds on top what the field can't hold: typo matching, idiom
  skipping, body phrases and the meaning check.
- A test fails if the two searches disagree on a shared phrase.

Some emergencies have no guide choice to point at yet (drowning, electric shock, trapped or crushed): those would need
new guide content first.

## How it was tested

- **Our own sets:** 362 invented questions over 159 topics (253 clean, red/yellow/green, 22 counterexamples like
  "brake bleed", 109 panicky typos), 52 multi-message conversations, #154's 32, #128's 52 including its reviewer's
  counterexamples, #241's 21, 48 glued messages. Each lists the words a useful page must contain and a page that must not
  come first.
- **Three independent lists,** written by agents with no knowledge of the code, told not to open any project file:
  690, 606 and 531 messages, labelled by urgency as an emergency nurse would, covering typos, glued words, slang,
  non-native English, voice dictation, emergencies buried in small talk, misconceptions, personas (a teenager texting,
  a parent at 3am, an elderly one-finger typist, someone in shock, someone who plays everything down), and 128–147
  counterexamples each. Fixes were built against list 1, checked on list 2 (later, a few slang words and contractions
  were taken from list 2, so it is no longer fully blind; its 92% is from before that); the meaning check was built
  from its own examples and checked on lists 1–3.
- **A fourth list, from Qwen3.5-9B run locally (not Claude):** 832 messages, 525 of them Chilean and Mexican Spanish, mostly
  idioms ("me muero de…", "estoy muerto…"), and 300 English (half of them one template). Narrow, but the first test of
  Spanish through the chat's path, where the local AI first writes English search words: red recognised 27% as typed
  → 96% (43/45) with them, an emergency book in the top 3 for 82% (hybrid); Spanish idioms flagged 7% → 19% (the
  translation turns "estoy muerto" into "dead"). It also found a fault, fixed since: untranslated words passed as
  English ("respirar humo incendio"); with the fix, 44/45.

| Red messages recognised as urgent | List 1 | List 2 | List 3 |
|---|---|---|---|
| Word rules before the held-out fixes | 85% | 85% | – |
| Word rules after | 99% (built on it) | 92% | 87% |
| Word rules + meaning check | 99% | 98% | **94.5%** |

- **Live tests** with a local Gemma 4 E4B on a desktop (2026-11-20 and 21): vague chest pain, glued and mistyped
  messages ("helpicutmynhanbditsbleedin"), an anaphylaxis sequence to the EpiPen, a nonsense question inside an
  urgent conversation, a shelter question. The answers cited the library and were judged good; the meaning check fired
  on the chest pain, the peanut reaction and both EpiPen messages. Once the model missed that the person typing was
  the injured one. Seen there and reported separately: the start of the local AI (#323) and the scroll after an answer (#324,
  PR #325). Not yet seen live: a correction message or a new emergency in the middle of a conversation.
- Upstream's tests, including #241's guide-search tests, pass. Two upstream tests fail on Windows only, before and after
  these changes (`test_battery`: a file name with ":"; `test_run_source_linux`: a Linux shell script).

## What is not solved

- **About 1 red in 18 on unseen wording is still missed,** mostly cases that need a clinician's inference with no alarm
  word: "a curtain coming down over my vision", "bit of a headache. worst one ive ever had", "ive written the notes and
  given my cat to my sister", a fever two days after chemo.
- **False alarms are high:** 70–75% of counterexamples on lists 2 and 3 are flagged urgent by words + meaning (61–69% by the words alone) ("bleed the
  brakes" is cut, new idioms are not). A false flag only means pages are always shown, so the cost is low, but it is
  not precise.
- **Most of it was written by one model family:** the word rules, the meaning check's examples and test lists 1–3.
  List 4 came from another (Qwen3.5-9B), but it is narrow (mostly Spanish idioms). Real people, especially non-native and
  voice users, may score lower.
- **English only** for the typo rules and the meaning check. Other languages work only through the local AI's English
  search words (list 4); without a local AI, a Spanish emergency is recognised about a quarter of the time.
- Typo correction cannot fix a typo that is another real word, except a short explicit list ("puls", "sea sure",
  "can't breed").

## Related work upstream

- **#302 (Miixms99, on #154):** a fallback for searches that name drowning, hypothermia or carbon monoxide, in review.
  Same problem, one condition at a time. PR 1 below is offered as its complement: the question sets and lists would
  show where the fallback helps and where it doesn't, and give the Medium-pack comparison asked for there.
- **#168 (kilid69):** an embed op in `lastbook_llm.cpp` for meaning-based search on a Mac. The fork's `--embed` mode is
  the same runner change; PR 5 should build on #168's op (or be folded into it), not compete. It will still clash:
  with the urgency PR a meaning model runs by default on every question.
- **#317 (nexdotworks) and #227 (domfahey):** meaning-based search on every platform (bge-small, sqlite-vec and
  question variants, with a repro kit), and on a Mac through the runner (EmbeddingGemma). Same direction, different
  use: they rank pages by meaning; here meaning only screens the question for urgency, and ranking stays as the app has
  it (keyword-only, or hybrid where it already runs). The maintainers asked to weigh #317 alongside #168 and #227. The
  test set and the blind lists could be run against those setups too.
- **#287 (wgl444):** guide search tries other word forms when nothing is found. PR 3 does this for the library search;
  the two should follow the same rules.

## Proposed PRs, in order

Each small, each scored against the same baseline on current `main`:

1. **Library-search test set and scorer** (the complement of #241, which covers the guides, and of #302): the question
   sets, the three independent lists, the scorer, a recorded baseline per commit. No code change. Offered on #154 first.
2. **Long pages in sections,** for saved web pages and for encyclopedia articles (best section, shown apart).
3. **Typo correction:** library words, English guard, contractions, glued words.
4. **Never withhold pages,** and the confidence estimate with buttons.
5. **Runner `--embed` mode** (C++ only), aligned with #168.
6. **Urgency on one source:** `urgent` phrases for the guide choices (guides PRs), the library search reading them, the
   meaning check on top, and the test that keeps the two searches together.
7. **Conversation handling,** for the local AI chat.

## Before the PRs

- [x] Live test on the PC with Gemma (2026-11-20, 21). Left: a correction and a new emergency mid-conversation.
- [x] Hugging Face: published at https://huggingface.co/STAirye/lastbook-meaning-red (commit 591b1b9), pinned in the
      manifest; a fresh download matched both checksums.
- [x] **Linux build** (2026-11-21, Debian 13 in Docker). The runner builds, its `--embed` mode works, the .deb builds,
      and upstream's smoke test passes. Not covered: that build did not bundle the meaning check's model files.
- [ ] **Mac build.** The runner and the app have not been built on a Mac. This needs a Mac, or the maintainers.
- [x] The English word list's licence: the verbatim copyright section of Chromium's `README_en_US.txt`.
- [x] The 15 slang, brand and medical words the typo corrector leaves alone ("unalive", "fortnite", "stooling"…)
      were found in independent list 2: kept, and marked as such in `engine/typos.py` (list 2 is in-sample for them).
- [x] Map the urgency rules onto #167's `urgent` field: measured (above); the phrases are drafted in
      `.claude/drafts/urgent-mapping/proposed_urgent.json`.
- [ ] Each PR on its own branch off current `main` (1.1.14 is merged into the fork), everything rerun there.

## References

- Fork record: `docs/FORK.md` §3g–3n on `STAirye/lastbook`, branch `fork/lightweight-gemma-no-us-maps`; finished
  work's scripts in `docs/evanesced/` (encyclopedias: `encyclopedias-3n/`).
- Upstream: issue #154 (search tiers), PR #167 (`urgent` field) and e2fa394 (its pruning), PR #168 (meaning-based search
  on a Mac), PR #241 (guide search tests), PR #302 (emergency fallback), PR #287 (word forms in guide search), PR #128
  (closed; its examples are in the test set), issues #261 and #262 (emergency numbers, nearest emergency room).
- Methods: [upstream-search-methods.md](upstream-search-methods.md).
- Detailed write-ups (local, to be attached to PR 1): `.claude/drafts/triage/` (RESULTS, COMPARE_*, MULTITURN,
  CONFIDENCE, AB_PHRASES, BODY_SIGNS, LESSONS_154), `.claude/drafts/independent*/RESULTS.md`,
  `.claude/drafts/meaning/` (RESULTS, LLAMACPP_SMOKE, LLAMACPP_STATS), `.claude/drafts/urgent-mapping/RESULTS.md`,
  `.claude/drafts/independent4/RESULTS.md`.

## Sources

1. American College of Surgeons Committee on Trauma, *Resources for Optimal Care of the Injured Patient* (2014),
   chapter 3, p. 28. https://www.rumcsi.org/wp-content/uploads/2020/09/Resources-for-Optimal-Care-2014-v11-1.pdf
